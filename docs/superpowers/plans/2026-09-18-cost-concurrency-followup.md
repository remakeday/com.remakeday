# 비용 동시성 후속 — 밤 제출 · 회차 시작 · 낮 장면 잠금 (휴먼테스트 순서표 5b)

등급: **A (비용)**. 구현 에이전트는 계획+구현, 검토는 컨트롤러가 별도(sonnet → opus).

근거: 신의 질문 개선(`2026-09-18-god-question-improvements.md`) opus 최종 리뷰 C1과 "보고만(범위 밖)" 3건.
C1에서 정한 원칙을 그대로 넓힌다 — **잠금은 기다리지 않는다(NOWAIT)**. 앞 요청이 모델 응답을 기다리며 행을 쥐고 있으면
뒤 요청은 곧바로 409를 받고 연결을 돌려준다. 기다리는 요청이 요청 풀을 채워 전역 DoS·감사 기록 롤백으로 번지지 않는다.

## 대상별 현재 동작

### 1. `POST /nights/{night_id}/submit` (`NightInteractor.submit`)

- 잠금 없음, 트랜잭션 경계 없음. `night.submitted` 검사 → 채점 모델 호출(참 명제 수 × 재생성 최대 3, 스레드 4개) → 기록.
- 동시 제출 N번은 모두 `submitted=False`를 보고 통과한다 → **채점 모델 호출 N배**, `answer_scored`·`loop_end`·`death` 이벤트 N벌.
- 저장소마다 `save_game_changes`가 곧바로 커밋한다(장면 트랜잭션 밖) → 중간 실패 시 일부만 커밋(노트 upsert 커밋이 더티한 밤·회차 속성까지 함께 커밋).
- 라우터 속도 제한 버킷 없음.

### 2. `POST /sessions/{attempt_id}/loops` (`LoopInteractor.start_loop`)

- `scene_transaction()`을 행 없이 연다 — 트랜잭션 경계만 있고 잠금 없음.
- 동시 요청 둘이 모두 "이전 회차 닫힘"을 보고 새 회차를 INSERT한다. `loops(attempt_id, loop_n)` 유일 제약 때문에 뒤 요청의 INSERT가
  **앞 요청이 planner 모델 응답을 받고 커밋할 때까지 연결을 쥔 채 기다린다** → 이후 `IntegrityError` → 500.
- planner 중복 호출은 INSERT가 planner보다 앞이라 일어나지 않는다(재현 테스트로 확인). 문제는 대기 중 연결 점유(C1 구조)와 500.
- 프론트(`app/play/page.tsx` `startLoop`)는 `loopAction.busy`로 중복 클릭을 막고, 실패는 기본 오류 토스트(재시도 버튼).

### 3. 낮 장면 `SceneTransaction` (발화·다음 장면·원숭이손 응답)

- 회차 행 `with_for_update()`(기다림) + 잠금 안 모델 호출(발화 NPC·분류, 장면 점검 매니저).
- 같은 회차 동시 요청은 앞 요청의 모델 응답 시간만큼 연결을 쥐고 기다린다. 다음 장면·원숭이손 응답에는 버킷도 없다 → 한 사용자가 병렬 요청으로 요청 풀을 채울 수 있다.
- 기존 계약: 같은 `request_id` 발화가 동시에 도착하면 기다렸다가 저장된 같은 응답을 돌려준다(`test_concurrent_retry_executes_model_and_charges_only_once`).
- 프론트(`DayScreen.tsx`): `mutationInFlight`로 화면 안 중복은 막는다. 겹칠 수 있는 건 네트워크 오류·게이트웨이 시간 초과(상태 0·5xx) 뒤 서버는 아직 처리 중인데 사용자가 "다시 보내기"를 누른 경우뿐이다. 이때 5xx·0이면 보낸 질문(`pendingUtterance`, 같은 `request_id`)이 남아 재전송된다. 4xx면 보낸 질문을 지우고 입력창에 문장을 되돌린다(새 `request_id`로 다시 보내게 됨).

## 설계

### 잠금 (Template Method — `scene_transaction.py`)

`SceneTransaction`의 잠금 단계를 NOWAIT 공통 헬퍼(`_lock_row`)로 올리고, 하위 클래스는 잠글 행만 정한다.

| 트랜잭션 | 잠그는 행 | 잠금 모드 | 쓰는 곳 |
|---|---|---|---|
| `SceneTransaction` | 회차 | `FOR UPDATE NOWAIT` | 발화·다음 장면·원숭이손 응답 |
| `NightTransaction` | 밤 (+ 회차 다시 읽기) | `FOR UPDATE NOWAIT` | 신의 질문·규칙 선택(기존), **밤 제출(신규)** |
| `AttemptTransaction` (신규) | 판 | `FOR NO KEY UPDATE NOWAIT` | **회차 시작** |

- 판 행은 회차·노트·규칙이 외래 키로 참조한다. 외래 키 검사는 `FOR KEY SHARE`를 잡으므로 `FOR UPDATE`면 판에 행을 넣는 다른 열린 트랜잭션과 괜히 부딪힌다. `FOR NO KEY UPDATE`는 회차 시작끼리·판 상태 UPDATE와는 충돌하고 외래 키 검사와는 충돌하지 않는다.
- 잠금 실패(`LockNotAvailable`)는 포트의 `RowBusy`로 올린다(기존).

### 1. 밤 제출

- `NightInteractor`에 `night_transaction` 포트(기본 `nullcontext`, 컴포지션 루트가 `NightTransaction(session)` 주입). `submit` 전체를 밤 행 잠금 안에서 한 커밋으로.
- 잠금을 얻은 뒤 밤·회차를 다시 읽으므로(`populate_existing`) 앞 제출이 커밋한 `submitted=True`를 본다 → "이미 제출했다" 409.
- 처리 중이면 `RowBusy` → `GameStateError("제출한 답을 채점하는 중이다. 잠시 기다려라.")` → 409.
- 부수 효과: 제출이 원자적이 된다(중간 실패 시 전부 롤백, 모델 호출 감사는 기존 규칙대로 전용 엔진에 남는다).
- **버킷은 걸지 않는다.** 잠금 + `submitted`로 한 밤 채점은 성공 1회로 묶이고, 밤은 판당 5개, 판은 하루 한도·`/sessions` 버킷으로 묶인다. `actions` 버킷을 공유하면 대화를 빨리 한 플레이어의 제출이 429로 막힐 수 있다(제출은 한 밤 1번뿐인 중요 단계). 별도 설정값 추가는 요청 범위 밖.

### 2. 회차 시작

- `LoopInteractor`에 `attempt_transaction` 포트(기본 `nullcontext`, 컴포지션 루트가 `AttemptTransaction(session)`). `start_loop`는 판 행 잠금 안에서.
- 처리 중이면 409 `"하루를 준비하는 중이다. 잠시 뒤 다시 시도해 주세요."`. 앞 요청이 커밋한 뒤 온 중복은 기존대로 "이전 회차가 아직 닫히지 않았다" 409.
- **기존 회차 반환은 하지 않는다.** 응답에 1장면 서술·관찰·지나가는 대사가 들어가 재구성이 필요하고, 프론트는 `busy`로 중복을 이미 막는다. 409 토스트면 충분하다.
- 버킷 없음 — 회차는 판당 5개, planner는 회차당 1회.

### 3. 낮 장면

- `SceneTransaction`을 NOWAIT로. 처리 중이면 `RequestInFlight`(`loop_interactor.GameStateError` 하위) → 라우터가 409 `{"code": "request_in_flight", "detail": ...}`.
  - 발화: "앞 대화를 처리하는 중이다. 잠시 뒤 같은 질문을 다시 보내 주세요."
  - 다음 장면·원숭이손 응답: "앞 요청을 처리하는 중이다. 잠시 뒤 다시 시도해 주세요."
- 멱등 재시도 계약 변경: 같은 `request_id`가 **처리 중에** 도착하면 기다리지 않고 409 `request_in_flight`. 앞 요청이 커밋한 뒤 같은 ID로 다시 보내면 저장된 같은 응답(모델 호출·차감 1회). 비용 쪽은 이전과 같다.
- 프론트 최소 변경:
  - `useApiAction`의 `onFail`에 두 번째 인자 `code`를 넘긴다(기존 호출부는 무시하므로 호환).
  - `DayScreen.tsx` 발화 `onFail` 한 줄: 4xx여도 `code === "request_in_flight"`면 보낸 질문(같은 `request_id`)을 지우지 않는다 → 기존 "다시 보내기" 버튼이 같은 ID로 재전송해 저장된 답을 받는다.
  - 다음 장면·원숭이손은 바꾸지 않는다: 오류 토스트 + 재시도. 다음 장면은 원래 멱등이 아니며(기다리는 잠금에서도 재시도는 한 장면 더 넘어갔다), 처리 중 중복은 이제 409라 오히려 두 번 넘어가지 않는다.
- 짧은 자동 재시도는 넣지 않는다 — 모델 응답이 수 초라 짧은 재시도는 대개 다시 409이고, 타이머·취소 로직이 낮 화면(내일 재구성 예정)에 붙는다.

## 테스트 (TDD — 수정 전 실패 확인)

실제 DB 세션 둘 + 스레드 + 컴포지션 루트 배선. 앞 요청을 이벤트로 잠금 안(모델 호출)에 세워 두고 뒤 요청을 보낸다.
뒤 요청이 돌아온 순간 앞 요청이 아직 멈춰 있으면(`first_still_held`) "기다리지 않음". 10초는 실패 시에만 닿는 안전 상한.

| 테스트 | 수정 전 기대 실패 | 수정 후 |
|---|---|---|
| 밤 제출 둘 동시 (`test_scene_transaction.py`) | 뒤 제출도 채점 → 모델 호출 2배, dict 반환 | 뒤 제출 즉시 409, 모델 호출 1벌, `answer_scored` 1개 |
| 회차 시작 둘 동시 (`test_scene_transaction.py`) | 뒤 요청이 INSERT에서 앞 요청 끝까지 대기 → 500 계열 `IntegrityError` | 즉시 409, planner 1회, 회차 1개 추가 |
| 다음 장면 둘 동시 (`test_scene_transaction.py`) | 뒤 요청이 대기 후 한 장면 더 진행 | 즉시 409 `RequestInFlight`, 장면 1칸만 |
| 같은 `request_id` 발화 동시 (`test_npc_dialogue_contract.py`, 기존 테스트 계약 변경) | 뒤 요청이 기다렸다가 같은 응답 | 즉시 409 `RequestInFlight` → 앞 요청 뒤 같은 ID 재전송이 같은 응답, 모델 호출·차감 1회 |
| 라우터 매핑 | — | `request_in_flight` 코드 409 |

## 범위 밖 · 남은 위험 (보고)

- 제출 결과 멱등 반환 없음: 네트워크 실패 뒤 재제출은 "이미 제출했다" 409(기존과 같음).
- `edit_claims`는 잠그지 않는다(모델 호출 없음). 채점 중 수정이 끼면 채점한 문장과 저장 문장이 어긋날 수 있다(화면은 채점 중 버튼 비활성).
- `start_loop` 네트워크 실패 뒤 재시도는 "이전 회차가 아직 닫히지 않았다" 409(기존과 같음).

## 구현 결과

### 재현 (수정 전 → 수정 후)

| 테스트 | 수정 전 (레드, 약 41초) | 수정 후 |
|---|---|---|
| `test_second_submit_while_scoring_is_409_without_a_second_scoring` | 뒤 제출이 앞 제출 채점 중에 **채점을 끝까지 수행하고 dict 반환**(채점 2벌) | 즉시 409 "채점하는 중", `answer_scored` 1개·`evaluator_verdict` 감사 = 명제 수, 커밋 뒤 재제출은 "이미 제출했다" |
| `test_second_loop_start_while_planning_is_409_without_waiting` | 뒤 요청이 INSERT에서 **앞 요청 끝까지 대기**(안전 상한 10초) 뒤 `IntegrityError (attempt_id, loop_n) already exists` — planner 중복은 없음 | 즉시 409 "하루를 준비하는 중", planner 감사 1개, 회차 2 하나 |
| `test_next_scene_while_the_scene_is_running_is_409_without_waiting` | 뒤 요청이 대기 뒤 **한 장면 더 진행**(beat 3) | 즉시 409 `RequestInFlight`, beat 2 |
| `test_concurrent_retry_is_409_while_in_flight_and_same_id_retry_returns_the_stored_reply` (옛 `test_concurrent_retry_executes_model_and_charges_only_once` 계약 변경) | 뒤 요청이 대기 뒤 같은 응답 | 즉시 409 `RequestInFlight` → 커밋 뒤 같은 ID 재전송이 같은 응답, 모델 호출 1·예산 7 |
| `test_request_in_flight_maps_to_409_with_a_retry_code` | `RequestInFlight` 없음(ImportError) | 409 `{"code": "request_in_flight", "detail": …}` |

새 동시성 테스트 5개는 5회 반복 모두 통과(회당 약 0.9초).

### 변경 파일

- `backend/apps/engine/adapter/outbound/repositories/scene_transaction.py` — `_lock_row`(NOWAIT → `RowBusy`) 공통화, `SceneTransaction` NOWAIT, `AttemptTransaction` 신규(`FOR NO KEY UPDATE NOWAIT`)
- `backend/apps/engine/app/ports/output/scene_transaction_port.py` — 모듈 설명만
- `backend/apps/engine/app/use_cases/loop_interactor.py` — `RequestInFlight`, `_turn`, `attempt_transaction` 포트, 발화·다음 장면·원숭이손·회차 시작 메시지
- `backend/apps/engine/app/use_cases/night_interactor.py` — `night_transaction` 포트, `submit` → 잠금 안 `_submit`
- `backend/apps/engine/dependencies/engine_dependency.py` — `AttemptTransaction`·`NightTransaction` 주입
- `backend/apps/engine/adapter/inbound/api/v1/game_router.py` — `RequestInFlight` → 409 + `code`
- `frontend/lib/useApiAction.ts` — `onFail(status, code)`
- `frontend/components/screens/DayScreen.tsx` — 발화 실패 처리 한 줄(`request_in_flight`면 보낸 질문 유지)
- `docs/spec/api_contract.md` — 회차 시작·발화·다음 장면·제출 409 설명
- 테스트: `test_scene_transaction.py`(4개 추가), `test_npc_dialogue_contract.py`(1개 계약 변경, 안 쓰게 된 `ThreadPoolExecutor` import 제거), `test_usecase_day.py`(`make_day`에 `AttemptTransaction`)

### 검증

- 관련 pytest 21파일 **383 passed**: attempt_ownership·connected_investigation·domain_p1·e2e_flow·five_loop_rules·guards·journey_and_reveal·night_clue·npc_dialogue_contract·paw_wishes·question_rule_flow·remake_day·rule_enforcement·scene_illustrations·scene_transaction·usecase_day·usecase_night·paw_scene_execution·usecase_intervention·scenario_paw·event_log. 전체 pytest는 테스트 DB 공유로 돌리지 않음.
- `lint-imports` 4 kept, 프론트 `tsc --noEmit` 클린. 헤드리스 미실행.

### 남은 위험

- 제출 원자화의 반대편: 채점 뒤 DB 오류로 롤백되면 재제출이 채점을 다시 부른다(서버 오류에서만). 전에는 중간 커밋으로 `submitted=True`만 남고 회차가 전이되지 않아 판이 멈출 수 있었다.
- 밤 정리(`draft`)는 잠그지 않는다. 낮 요청이 회차 행을 쥔 동안 도착하면 외래 키 검사로 기다린다 — 낮 종료 뒤에만 부르므로 실제로 겹치지 않는다.
- 같은 밤 제출 중에 신의 질문이 오면 메시지가 "앞 질문에 답하는 중"(질문 쪽 문구)으로 나온다 — 화면 흐름상 겹치지 않는다.
- 다음 장면·원숭이손의 409 토스트 재시도는 기존처럼 멱등이 아니다(재시도 = 한 장면 더).

## opus 최종 리뷰 반영(수정 1회)

등급 A. 반영 6건(I1·I2·M1·M2·M3·M4), 보고만 I3·후속 5건. 이후 컨트롤러 범위 재검토.

### 변경

| 지적 | 변경 |
|---|---|
| **I1** 채점 중 청구문 수정이 잠금을 기다렸다 커밋 뒤 옛 `submitted=False`로 통과해 제출 답을 덮어씀 | `NightInteractor.edit_claims` → 밤 행 잠금(`NightTransaction`) 안 `_edit_claims`. 처리 중이면 409 `request_in_flight`, 잠금 뒤 다시 읽은 `submitted`·`edit_count`로 판정 |
| **I2** 채점이 게이트웨이 한도를 넘거나 연결이 끊기면 재시도가 409로 막혀 판을 잃음 | 제출 응답을 기록 전에 확정해 `AnswerScoredEvent.response`에 저장. `night.submitted`면 저장 응답을 그대로 반환(모델 호출 0), 저장 응답 없는 과거 제출은 409 "이미 제출했다". 밤 단서 응답은 `_night_clue_view`(시나리오 데이터·이번 결말로만 결정)로 분리 — 이벤트 기록 순서는 그대로 |
| **M3** RowBusy → 도메인 예외 변환 3벌 | `scene_transaction_port.one_request_per_row(transaction, row_id, busy_cls, message)` 하나로. 포트에 `RequestInFlight` 표지 예외, 낮·밤·신의개입이 각자 `class RequestInFlight(GameStateError, 포트 RequestInFlight)` — 기존 `GameStateError` 판정 유지. 라우터는 포트 `RequestInFlight`를 `_STATE_ERRORS`보다 먼저 잡는다(순서 유지). `loop_interactor._turn`·`intervention_interactor._night_turn` 제거 |
| **M1** 회차 행 `FOR UPDATE`가 그 회차를 참조하는 INSERT의 외래 키 검사와 부딪힘 | `SceneTransaction._lock` → `FOR NO KEY UPDATE NOWAIT`(`key_share=True`) |
| **M2** 감사 엔진 끊긴 연결 | `get_audit_engine`에 `pool_pre_ping=True` |
| **M4** 테스트 공백 | 아래 표 |

- 밤 정리(`draft`)는 잠그지 않는다. 근거: `loop.state == "night_pending"`일 때만 통과하고, 이 상태는 낮 마지막 `advance_beat`가 커밋한 뒤에만 생긴다. 이후 낮 요청(발화·다음 장면)은 잠금 직후 상태 검사에서 모델 호출 없이 거절돼 회차 행을 오래 쥐지 않는다. 밤 행은 아직 없으므로 제출·수정·질문과 겹칠 행도 없다. M1로 정리의 밤 INSERT가 낮 잠금과 부딪히지 않는다. 남는 것은 정리 중복 클릭의 `nights.loop_id` 유일 제약 충돌(모델 호출 없음, 수 ms 대기 뒤 500) — 비용 문제 아님, 범위 밖.
- 프론트 코드 변경 없음. 제출 실패는 기존 `ConfirmScreen`의 오류 토스트 + "재시도" 버튼이다. 채점 중이면 서버 문구가 "잠시 뒤 다시 시도해 주세요"로 안내하고, 채점이 끝난 뒤 재시도는 저장 응답 200 → 기존 `onSubmitted` 흐름으로 넘어간다. 자동 재시도 루프는 넣지 않는다: 채점은 수십 초가 걸릴 수 있어 짧은 간격은 대개 다시 409이고, 긴 간격·최대 횟수·언마운트 정리가 확인 화면에 붙는다. `play/page.tsx`에는 제출 실패 처리가 없다(성공 콜백만).

### 재현 (수정 전 → 수정 후)

| 테스트 (`test_scene_transaction.py`) | 수정 전 | 수정 후 |
|---|---|---|
| `test_edit_claims_while_scoring_is_409_and_keeps_the_submitted_claims` | 수정이 채점 끝(안전 상한 10초)까지 대기 뒤 통과 — 저장 문장 `["바꾼 문장."]`·`edit_count=1`·`submitted=True` (제출 답 덮어씀) | 즉시 409 `RequestInFlight`, 저장 문장·`edit_count=0` 그대로, 채점 뒤 수정은 "수정은 1회만" |
| `test_resubmit_after_commit_returns_the_stored_result_without_scoring_again` | `GameStateError("이미 제출했다")` | 첫 응답과 같은 dict, 모델 호출·`evaluator_verdict` 감사·`answer_scored`·`death` 추가 0 |
| `test_submitted_night_without_a_stored_result_stays_409` | (통과 — 기존 동작 고정) | 409 "이미 제출", 모델 호출 0 |
| `test_submit_in_flight_carries_the_retry_code` | 포트 `RequestInFlight` 없음(ImportError) | 채점 중 재제출이 밤 `GameStateError`이자 포트 `RequestInFlight` |
| `test_day_scene_loop_lock_does_not_block_foreign_key_inserts` | 다른 세션 밤 INSERT가 `LockNotAvailable`(lock_timeout 2초, `FOR KEY SHARE OF loops`) | 곧바로 INSERT, 장면은 1칸 |
| `test_loop_start_attempt_lock_does_not_block_note_inserts` | (통과 — `AttemptTransaction`이 이미 `FOR NO KEY UPDATE`, 공백 보강) | 곧바로 노트 INSERT, 회차 2 |
| `test_every_in_flight_error_maps_to_409_with_the_retry_code[loop/night/intervention]` | night·intervention에 `RequestInFlight` 없음 | 셋 다 409 `{"code": "request_in_flight", …}` |

기존 `test_second_submit_while_scoring_is_409_without_a_second_scoring`에서 "커밋 뒤 재제출은 이미 제출했다" 단언을 뺐다(I2 계약 변경, 새 재제출 테스트로 이동).

### 검증

- 관련 pytest 21파일 **392 passed**(위 구현 결과와 같은 목록). `test_scene_transaction.py` 16개 5회 반복 모두 통과(회당 약 1.4초).
- `lint-imports` 4 kept, 프론트 `tsc --noEmit` 클린. 헤드리스·모델 호출·서버 재시작 없음.

### 보고만 (범위 밖)

- I3 `.env` 하루 판 한도 복귀 — 컨트롤러가 제출 체크리스트에 기록.
- 발화 모델 실패 무료 반복(`loop_interactor` `DialogueUnavailable`), 다음 장면·제출·회차 시작 사용자 단위 버킷, 채점 모델 실패 시 0점 커밋·재채점 불가, 회차 시작 타임아웃 복구, 요청 풀 크기.
- 저장 응답의 `intervention_available`는 제출 시점 값이다. 규칙을 고른 뒤 같은 밤을 다시 제출하면 옛 응답(true)을 받는다 — 화면 흐름상 제출 화면으로 돌아가지 않는다.
- 밤 정리 중복 클릭은 `nights.loop_id` 유일 제약으로 500(모델 호출 없음, 기존과 같음).
