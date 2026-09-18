# API 계약 v1 (MVP) — backend 8500 / frontend 3500

모든 응답은 JSON. 에러는 `{detail: string}` + 4xx/5xx. 잘못된 상태 전이는 409.

## 세션·회차 (P1)

### POST /sessions
req: `{prior_attempt_id?: string}` (UUID 문자열 — 형식이 아니면 422)
res: `{attempt_id: string, attempt_n: number, entry_lines: string[3], prior_cell_results: CellScores|null}`
- `prior_attempt_id`는 요청 사용자의 판일 때만 이어진다. 남의 판 ID는 없는 판처럼 무시한다 — 에러 없이 200, 새 판은 `attempt_n: 1`, `prior_cell_results: null` (F26).

### POST /sessions/{attempt_id}/loops
res: `{loop_id: string, loop_n: number, morning_text: string, damage_level: 0|1|2|3, budget_left: number, beat: 1, beat_title: string, narration: string, broadcast: string|null, illustrations: Illustration[], aftermath: string|null, lines: Line[]}`
- 회차 1..5 순서 강제. 이전 회차가 안 닫혔으면 409
- 409 `request_in_flight` (2026-09-18, 5b): 같은 판의 회차 시작이 처리 중(planner 모델 응답 대기)이면 기다리지 않고 곧바로 `{"code": "request_in_flight", "detail": "하루를 준비하는 중이다. …"}`. 모델 호출·회차 생성이 없다.
- `aftermath`: 전날 걸린 규칙이 부작용을 만들었을 때만 — "어제는 없던 일이 있었다" 톤 한 줄 (내용은 밝히지 않는다)
- `lines`: 대사창 줄 목록(2026-09-18, 낮 화면 VN). 순서는 장면 서술 → 방송 → 행동·규칙 결과·설명·부작용 → 인물 혼잣말(`ambient`) → 단서 조각 → 기록 알림(`system`). `narration`은 `scene`·`action`·`rule_result`·`statement`·`paw_effect` 줄의 `text`를 공백으로 이은 것과 같다. 기존 `narration`·`broadcast`·`ambient`는 그대로 둔다.
- `Illustration`: `{image_id: string, caption: string}`. 시나리오가 지정한 현재 비트의 관찰 이미지 목록. `image_id`는 프론트의 허용된 이미지 매핑 키이며 URL·LLM 출력이 아니다. 이미지 없는 비트는 빈 배열. 프론트는 필드가 없는 구버전 응답과 알 수 없는 ID에 기존 비트 배경을 사용한다.

### POST /loops/{loop_id}/utterances
req: `{target: string(code), text: string, request_id?: string(UUID)}`
res: `{utterance_id: string(UUID), reply: string, npc: {code: string, name: string, mood: "calm"|"uneasy"|"wary", uttered: boolean}, budget_left: number, beat: number, tool_used: boolean, observations: Observation[], gated?: boolean, lines: Line[]}`
- `lines`: 답변을 문장 단위로 나눈 `npc` 줄(따옴표 안 마침표는 나누지 않음, `observation_id`는 답변 관찰). `gated=true`면 대체 문장 하나가 `system` 줄이다.
- 한 장면에서 NPC마다 성공한 대화는 1회만 가능하다. `uttered=true`인 NPC에게 새로운 질문을 보내면 409이며 예산은 줄지 않는다. 다른 NPC는 대화 가능하고, 다음 장면에서 다시 말을 걸 수 있다. 성공한 질문마다 예산 1회를 쓰며 장면은 이동하지 않는다.
- `gated=true`: 무의미한 입력이라 판단해 인물의 실제 반응 대신 대체 문장(`reply`)을 돌려준 응답. `npc.uttered`는 항상 `false`라 이 비트의 재발화 잠금이 걸리지 않는다. `observations`는 빈 배열이다. 예산은 같은 비트의 첫 무의미 입력에서는 차감되지 않고, 두 번째부터 차감된다(`budget_left` 반영). `gated` 필드가 없으면 구버전 응답이거나 정상 발화로 취급한다.
- 같은 회차의 같은 `request_id`/대상/질문은 장면당 1회 제한과 무관하게 저장된 성공 응답을 반환하고 추가로 차감하지 않는다. 다른 질문에 ID를 재사용하면 409. ID 생략 요청은 각각 새 발화다.
- 예산 소진·대화할 수 없는 상대·낮 종료는 409. 모델 응답 실패는 503이며 예산·대화 기억·노트가 변경되지 않는다. 네트워크 오류 후에도 같은 질문과 ID로 재전송한다.
- 발화·예산·관찰·노트를 한 트랜잭션으로 저장한다. 발언별 관찰 ID는 서로 다르며 응답의 관찰 ID로 노트와 연결한다.
- 409 `request_in_flight` (2026-09-18, 5b): 같은 회차의 앞 요청(발화·다음 장면·원숭이손 응답)이 처리 중이면 기다리지 않고 곧바로 `{"code": "request_in_flight", "detail": "앞 대화를 처리하는 중이다. …"}`. 같은 `request_id`가 처리 중에 다시 와도 409이며, 앞 요청이 끝난 뒤 같은 ID로 다시 보내면 저장된 응답을 받는다(모델 호출·차감 1회). 프론트는 이 코드에서 보낸 질문을 지우지 않는다.

### POST /loops/{loop_id}/beats/next
res: `{beat: number, beat_title: string, narration: string, broadcast: string|null, illustrations: Illustration[], paw_offer: {offer_id: string, rule_label: string, shown_reason: string|null}|null, day_done: boolean,
      ambient: {lines: {code: string, name: string, text: string}[]}|null,
      note_found: {id: number, kind: string, text: string}|null, lines: Line[]}`
- `lines`: 회차 시작과 같은 순서의 대사창 줄. `day_done=true`면 빈 배열.
- day_done=true면 이후 발화·비트 넘기기 409, 밤으로
- 같은 회차의 앞 요청이 처리 중이면 곧바로 409 `request_in_flight` (발화 절과 같은 잠금). 원숭이손 응답도 같다.
- `illustrations`: 현재 비트만 전달하며 낮 종료 시 빈 배열. 장면 넘겨 보기는 발화 예산·비트 진행에 영향을 주지 않는다. 폐쇄 이미지는 이 목록에 넣지 않고 밤의 `world_outcome=closure`에서만 표시한다.
- `ambient`: 실제 발생한 행동과 참여 인물 조건을 충족한 시나리오의 작성 대화. 참여자 기억에 발언별로 저장한다. 조건을 충족하지 못하면 null (발화 예산 무관).
- `note_found`: 이 비트에서 새로 발견된 감각 파편 (노트에 적힌 직후)

### POST /loops/{loop_id}/paw/respond
req: `{offer_id: string, accept: boolean}`
res: `{applied: boolean, rule_label: string|null, narration: string|null, illustrations: Illustration[], observations: Observation[], lines: Line[]}`
- `lines`: 수락 즉시 장면에서 새로 생긴 줄만(`narration`과 같은 내용). 뒤 비트 소원이거나 거절이면 빈 배열.
- `paw_offer.rule_label`(beats/next)과 수락 응답의 `rule_label`은 시나리오 소원 문장이다(예: "채연이 오늘은 밥을 왜 안 먹는지 솔직하게 말한다."). `shown_reason`은 관리자 제안 문구(A/B로 null 가능).
- 수락하면 보이는 규칙 1개(`source=monkey_paw`)와 숨은 규칙(`source=paw_effect`)이 판 단위로 저장된다. 숨은 규칙은 `start_loop.active_rules`에 나오지 않는다.
- 수락 즉시 장면: 소원 장면 비트가 현재 비트면 그 장면을 바로 실행하고 새로 생긴 서술·삽화·관찰만 `narration`/`illustrations`/`observations`에 싣는다. 뒤 비트 소원이거나 거절이면 `narration=null`, 빈 배열. 이미 공개된 장면 관찰·노트는 중복되지 않는다. 지나가는 대사는 재생하지 않는다.
- 발화 예산은 소원 수락·반대 사건 어디에서도 줄지 않는다. 반대 사건이 그날 전부 일어난 경우에만 마지막 반대 사건 비트에 부작용 관찰 문장이 `rule_result` 관찰로 공개된다.
- 오퍼 없음·다른 offer_id는 409.

### GET /loops/{loop_id}/notes
res: `{notes: [{id: number, kind: "fragment"|"confirmed"|"rule_observation", text: string, loop_n: number}]}`

### GET /loops/{loop_id}/npcs
res: `{npcs: [{code, name, mood}]}` (대화 가능 인물만)

## 밤 (P2)

### POST /loops/{loop_id}/night/draft
req: `{tapped_note_ids: number[], free_text: string}`
res: `{night_id: string, claims: string[], is_question: boolean[]}` (≤8)
- 자유서술(`free_text`)만 문장·줄 단위로 나눈다. 8개를 넘으면 나머지를 마지막 항목에 모아 보존한다.
- 선택한 노트(`tapped_note_ids`)는 **채점 후보에 들어가지 않는다**(2026-09-17, 테스터9 F17·테스터11 O1). 저장만 되어 다음 밤 참고 목록의 표시 복원에 쓰인다. 기록 원문을 글에 직접 옮겨 적으면 그 문장은 주장이 된다.
- `free_text`가 비면 `claims=[]`로 정리된다(거절하지 않음, 점수 0). 화면은 글이 비면 제출 버튼을 막는다.
- `is_question`: `claims`와 같은 길이·순서. 질문형 문장(물음표, `~인가/~나/~까/~니/~냐/~는지` 어미) 표시용이며 채점에는 쓰지 않는다(테스터11 O2).
- 정리 단계는 LLM 요약이나 어휘 필터로 내용을 추가·폐기하지 않는다. 정오 판정은 제출 시 수행한다.

### PATCH /nights/{night_id}/claims
req: `{claims: string[]}` — **1회만**, 2번째 409
res: `{claims: string[], is_question: boolean[]}`
- 409 `request_in_flight` (2026-09-18, opus 리뷰 I1): 같은 밤의 제출이 채점 중이면 기다리지 않고 곧바로 `{"code": "request_in_flight", "detail": "답을 처리하는 중이다. …"}`. 저장 문장·수정 횟수가 바뀌지 않는다(채점이 끝난 뒤에는 제출한 밤이라 409 "수정은 1회만"). 수정 가능 판정은 밤 행 잠금을 얻은 뒤 다시 읽은 값으로 한다.

### POST /nights/{night_id}/submit
res: `{total: number, passed: boolean, loop_n: number, world_outcome: "truck"|"quiet"|"closure"|null,
      is_final: boolean, closed_by: "clear"|"doom"|"understood"|"understood_all"|null,
      cells: CellScores|null, cookie: {text: string, cell: string, level: 1|2|3}|null,
      intervention_available: boolean,
      ending_lines: string[]|null, cell_feedback: string|null, wrong_claim_count: number,
      accepted_claims: string[], empty_cells: ("cause"|"motive")[],
      night_clue: {loop_n: number, caption: string, image_ids: string[], voice_id: string,
                   broadcast: string, outcome_line: string|null}|null}`
- `total`: 상황 70점(원인35 + 동기35) + 정체30점. 부작용은 채점하지 않는다.
- 200 재제출 (2026-09-18, opus 리뷰 I2): 이미 제출한 밤에 다시 제출하면 처음 제출이 돌려준 응답을 그대로 돌려준다(채점 모델 호출·기록 없음). 게이트웨이 시간 초과·연결 끊김 뒤 재시도로 판을 잃지 않게 하려는 것이며, 값은 모두 제출 시점 기준이다(`intervention_available` 등도 그때 값). 저장 응답이 없는 과거 제출 밤(2026-09-18 이전)은 기존대로 409 `"이미 제출했다"`.
- 409 `request_in_flight` (2026-09-18, 5b·opus 리뷰 I2): 같은 밤의 앞 제출이 채점 중이면 기다리지 않고 곧바로 `{"code": "request_in_flight", "detail": "제출한 답을 채점하는 중이다. 잠시 뒤 다시 시도해 주세요."}` — 채점 모델 호출이 없다. 화면은 오류 토스트의 재시도로 잠시 뒤 다시 보내면 채점이 끝난 뒤 저장 응답(200)을 받는다. 제출 판정·채점 기록·회차 종료는 한 트랜잭션이다.
- `night_clue`: 밤 단서 시퀀스(밤단서 v2 P.1) — 결말 전환에서 관리자 밤 방송(`voice_id` MA08~12, 대본 `broadcast`) → 치지직 띠 안 `image_ids`(1~2장) → 바탕 위에 남는 `caption` 순서로 재생한다. 트럭 결말 밤에는 `outcome_line`(기존 트럭 파편)이 캡션 뒤에 한 줄 더 붙는다. 서버는 제출 시 `caption`을 「N회차 · 소등 후」 관찰(scene), `broadcast`를 전언(statement)으로 저장해 다음 밤의 근거로 탭할 수 있게 한다. 회차 표가 없는 시나리오는 null.
- `cell_feedback`: 매일 밤 — 칸별 점수는 숨긴 채 원인·동기 중 점수 > 0인 칸의 진행 문장만 ("원인은 조금 잡혔다." 톤. 잡혔다≥80% / 조금 잡혔다>0). 잡힌 칸이 없으면 null. 정체·부작용은 이름을 꺼내지 않는다(기획서 §4.8⑤ — 정체는 아무도 묻지 않는 질문). 2026-09-17 전에는 "…비어 있다"와 정체 칸도 담았다(테스터10 F1).
- `accepted_claims`: 매일 밤 — 이번 채점에서 `confirmed`·`partial`로 인정된 플레이어 문장(단조 잠금으로 유지된 판정 포함). 칸 구분 없이 플레이어가 쓴 순서대로, 중복 없이. 값은 이번 밤 채점 후보(`claims`를 문장 단위로 나눈 것) 중 판정이 실제로 지목한 후보만 고른다 — 채점기가 지목한 후보 번호, 잠금이면 직전 매칭 문장과 같은(공백·끝 문장부호만 무시) 이번 후보 하나. 정규화만 다른 두 후보 중 하나만 지목됐으면 그 하나만 나오고, 후보에서 찾지 못한 지목은 보정하지 않고 뺀다. 진실(정답 명제) 문장은 담지 않는다(`truth_reveal`은 계속 5회차만).
- `empty_cells`: 매일 밤 — 점수 0인 칸 코드. 원인·동기만. 화면이 "동기가 아직 비어 있다." 같은 칸 이름 힌트로 바꾼다. 회차별 단계 힌트는 없다.
- `wrong_claim_count`: 세계와 닿지 않은 주장 수 (감점 없음, 정보만)
- 1~4회차 → 점수 무관 is_final=false, intervention_available=true (신의개입으로)
- 5회차 → 점수 무관 판 종료(is_final=true, closed_by·cells·ending_lines 채움), intervention_available=false
- `passed`(≥50%)와 `closed_by`는 기존 분류 호환용이다. 생존·회차 종료·회고 접근 조건이 아니다.
- `world_outcome`은 모든 제출에서 세계 상태로 결정한다. 이해도가 100%여도 생존으로 바뀌지 않는다.
- `ending_lines`는 1~4회차에 null이다. 시나리오 결말 → 개발 회고 순서로 표시한다.
- `cookie`는 호환용 null이다. 점수에 따른 기존 쿠키 대신 모든 최종 점수에서 결말과 회고를 제공한다.
- 칸별 점수(cells)는 판 종료 때만 반환. 밤마다는 total만

## 신의개입 (P3) — 멸망한 밤에만

### POST /nights/{night_id}/questions
req: `{text: string}` → res: `{verdict: string, answer: string, detail: string|null, remaining: number, status: "supported"|"contradicted"|"unknown", evidence_ids: string[], evidence: Observation[], unlocked_note: null, next_observation: string|null, kind: "answer"|"guide", refunded: boolean}`
- `verdict`: "맞다." / "아니다." / "그건 알 수 없다." / "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."(왜/이유/어떻게 질문만)
- 판정은 3종으로 축소 — "그런 일은 없었다"는 기록 부재와 미발생을 혼동시킨다는 테스터1 소견(docs/review-verification/2026-09-09-first-play/tester1-findings.md)에 따라 제외.
- `answer`: 한다체 문장. 첫 문장은 verdict 또는 그 요지. 최대 3문장
- `unlocked_note`: 항상 null (호환성 유지)
- `next_observation`: 세계 구조 기반 조언 한 줄 — 항상 "네 기록의 「{닻 관찰 문장}」." 으로 시작하고 뒤에 "내일 {인물}에게 … 물어봐라." 또는 "{인물}: {행동} 규칙을 걸어 봐라."가 붙는다. 닻(플레이어 공개 관찰)이 없으면 null
- status="supported"일 때 kind "confirmed" 노트 저장(source_key `confirmed-{observation_id}`). 다음 밤 근거 목록에 확인 그룹으로 표시
- `refunded` (2026-09-18, 순서표 5번): `status="unknown"`인 답은 횟수를 차감하지 않는다(`remaining`에 반영). 단 같은 밤 환급 3회까지, 같은 밤에 이미 한 질문(공백·문장부호 무시)을 다시 물으면 차감한다. 모델 실패로 인한 unknown도 환급 대상이며, 모델이 답하지 못한 질문은 재입력 비교에서 빼고 환급 상한에는 센다(이벤트 `model_failed`). 한 밤 모델 호출은 최대 6회(재생성 포함 18회). 전에는 모든 답이 1회 차감.
- `kind="guide"` (2026-09-18, 테스터10 F5): 게임 목적·사용법 질문("이 게임이 뭐야", "목적이 뭐야", "멸망한다는 게 뭔 소리야", "뭘 해야 돼", "너에게 뭘 물어")은 규칙 표로 분류해 고정 안내 답을 준다. 모델 호출·판정(`verdict=""`, `status="unknown"`)·근거·조언·노트·횟수 차감이 없고 환급 상한도 쓰지 않는다. 인물 이름이 들어간 질문은 안내로 분류하지 않는다. 안내 답은 원인·동기를 밝혀 쓰는 게임이라는 수준까지만 말한다(정체·부작용 칸 언급 없음, 기획서 §4.4⑤). 안내 문답은 조언자 입력의 최근 문답 2쌍과 회고 `questions_asked`에 들지 않는다. 전의 meta 경로("너에게 … 물어/질문" → "맞다." 판정)는 이 사용법 안내로 대체됐다. 분류 표는 `docs/superpowers/plans/2026-09-18-god-question-improvements.md` §3(b).
- 공개 사다리 (2026-09-18): 시나리오 `advisor_ladder` 칸은 단계 `max(회차, 1 + 최고 총점의 25·50·75점 도달 수)` 이하일 때 열리고, 질문이 칸의 cue를 물을 때만 최대 2개가 조언자 입력에 공개 기록과 같은 자격으로 붙는다. 근거로 쓰이면 `evidence`에 `observation_id="ladder:{key}"`, `scene_title="세계에 알려진 사실"`, `beat=0`, `source_kind="scene"`인 Observation으로 나온다. 세계가 흘리는 공개 사실이며 숨은 진실·정답 주장·결말 문장이 아니다(기획서 §7.4). `status="unknown"` 답의 `evidence`·`detail`에는 사다리 칸을 넣지 않는다(판정 재료일 뿐 환급 답으로 원문을 주지 않는다). 화면은 사다리 근거를 회차·장면 없는 "세계에 알려진 사실" 카드로 따로 표시한다.
- 409 `request_in_flight` (2026-09-18, opus 리뷰 C1·M3): 같은 밤의 앞 요청(질문·규칙 선택)이 처리 중이면 기다리지 않고 곧바로 409 `{"code": "request_in_flight", "detail": "앞 질문에 답하는 중이다. …"}`(규칙 선택은 `"앞 요청을 처리하는 중이다. …"`). 모델 호출·차감·기록이 없다. 남은 질문 0은 코드 없는 409.
- 화면: 판정 배지 + 본문 첫 문장 먼저, `next_observation`은 "내일 해 볼 일" 블록으로 크게, 나머지 문장·판정 설명·근거 카드는 "자세히" 접기.

### GET /nights/{night_id}/options
res: `{options: [{index: 1|2|3, label: string}]}`

### POST /nights/{night_id}/rule
req: `{choice: "1"|"2"|"3"|"custom", custom_text?: string}`
res: `{ok: boolean, rule_label: string|null, conflicts: string[], reason: string|null}`
- ok=true 후 다음 회차 시작 가능 (POST /sessions/{id}/loops)
- 같은 밤의 질문·규칙 선택이 처리 중이면 곧바로 409 `request_in_flight` (위 질문 절과 같은 잠금)

## 판 종료 후 (P5)

### GET /attempts/{attempt_id}/harness — 5회차 제출 완료·판 종료 시 점수 무관 200, 아니면 403
res: `{rules: [...], harness_summary: {...}}`
- 진행 중 및 기존 조기 종료 기록은 403이다. 인스펙터 토큰 정책은 별개로 유지한다.
- `rules`: rule_id, source(monkey_paw/paw_effect/user_choice/user_custom), target, when_beat, effect, action, shown_reason, hidden_side_effect, created_loop, conflict.
- `harness_summary`: total_events, harness_interventions, fallbacks, paw_accepted, recommended_rules, custom_rules, rule_conflicts, questions_asked, rule_success_rate(null), tool_side_effects([{loop_n, beat, text}]).
- 추천/직접 규칙은 실제 저장된 규칙만 센다. 거부된 직접 제안은 포함하지 않는다. 충돌 개수는 모든 출처의 등록 규칙 기준이다.
- hidden_side_effect는 설계된 대가이며 발생 확인이 아니다. tool_side_effects는 도구 실행 기록 전체이며 원숭이손과의 인과관계를 확정하지 않는다.
- harness_interventions는 위반·폴백이 기록된 모델 호출 수다. 전체 호출 수 또는 사용자가 건 규칙의 성공률이 아니다. 규칙 이행 성공률은 아직 미측정이므로 null이다.

### GET /attempts/{attempt_id}/inspector — 헤더 `X-Inspector-Token: {INSPECTOR_TOKEN}`
res: `{events: [...], patches: [...], paw_rules: [...], scoring: [...]}`
- 로그인 불필요, 토큰 인증만. 토큰은 요청 헤더로만 받는다 — 쿼리스트링(`?token=`)은 받지 않는다(URL은 cloudflared·uvicorn 접근 로그와 브라우저 기록에 남는다). 비교는 상수 시간(`hmac.compare_digest`).
- **404** — `INSPECTOR_TOKEN`이 설정되지 않음(코드 기본값 없음). 헤더와 무관하게 라우트가 없는 것처럼 응답한다.
- **403** — 토큰 설정됨 + 헤더 누락·불일치.

### GET /health
res: `{db}` — `db`는 `ok | error`. 공개 경로(api.remakeday.com)라 기동 확인에 필요한 DB 상태만 준다. 모델·시나리오·하네스 구성은 노출하지 않는다(2026-09-18). 모델 구성 확인은 서버 `.env`(`get_settings()`)로 한다.

## 과잉 사용 방지 허들 (2026-09-16)

`GUARD_AUTH`가 `off`가 아니면(기본 `on`, `On` 같은 값도 켜짐) 로그인 쿠키(`rd_session`)를 요구한다. 로컬 개발·러너는 `--dev-login`을 쓴다. `GUARD_AUTH=off`는 8500이 아닌 포트로 띄운 러너 프로세스의 환경변수로만 주고 `backend/.env`에는 넣지 않는다(8500은 cloudflared로 공개돼 있다). Cloudflare를 거친 요청(`CF-Connecting-IP` 헤더 있음)은 off에서도 **403** `{"detail": "인증 우회 모드는 외부 요청을 받지 않는다"}`로 거부하고 `GuardEvent(layer="auth", reason="guard_auth_off_via_proxy")`를 남긴다.

- **401** — 로그인 필요. 요구 라우트에 `rd_session` 쿠키가 없거나 무효. 본문 `{"detail": "로그인이 필요하다"}`.
- **403** `{"code": "daily_attempt_limit", "detail": "오늘은 여기까지. 내일 다시 시작할 수 있다."}` — 이 사용자의 오늘 판 생성 수가 `USER_DAILY_ATTEMPTS`(기본 5)에 도달. `POST /sessions`에서만 발생.
- **429** `{"detail": {"detail": "요청이 너무 잦다", "retry_after": number}}`, 헤더 `Retry-After: {retry_after}` — 속도 제한 버킷 초과(`IP_SESSIONS_PER_MINUTE`/`IP_ACTIONS_PER_MINUTE`, 기본 5/30 분당).
- **503** `{"code": "daily_cap", "detail": "오늘 정원이 마감됐다."}` — 오늘 전역 판 생성 수가 `DAILY_ATTEMPT_CAP`(기본 200)에 도달. `POST /sessions`에서만 발생.
- **413** `{"detail": "요청이 너무 크다"}` — 요청 본문이 262144바이트(256KiB)를 넘음. `Content-Length` 헤더만 보고 본문을 읽기 전에 거부한다(ASGI 미들웨어, `main.py`). `Content-Length`가 없는 요청은 통과시킨다.
- **422** — 텍스트 상한 초과 시 FastAPI 기본 검증 에러(`detail`이 배열). 상한: `POST /loops/{loop_id}/utterances`·`POST /nights/{night_id}/questions`의 `text` 200자, `POST /loops/{loop_id}/night/draft`의 `free_text` 2000자, `PATCH /nights/{night_id}/claims`의 `claims` 배열 8개·각 500자, `POST /nights/{night_id}/rule`·`/rule/preview`의 `custom_text` 200자.

`attempts.user_id`: 판을 만든 사용자의 `users.id`(UUID). 세션의 `sub`(구글 sub, 개발 계정은 `dev:{id}`, `GUARD_AUTH=off`일 때는 `"dev"`)로 `users` 행을 찾아 그 `id`를 넣고, 판 주인 확인도 같은 경로(sub → `users.id` → `attempts.user_id`)로 맞춘다. 하루 판 수·전역 정원 집계의 기준. **FK 제약 없음** — 익명 구판(이 컬럼이 `null`인 기존 판) 호환을 위해 의도적으로 걸지 않았다.

### 공개 배포 설정 (F26b, 2026-09-17)

`FRONTEND_BASE_URL`이 `https://`로 시작하면 공개 배포 설정으로 본다(`Settings.public_deploy`, 세션 쿠키 `Secure` 판정과 같은 기준). 공개 배포 설정에서는:

- `GUARD_AUTH=off`면 서버가 기동을 거부한다(lifespan `RuntimeError`) — off는 모든 요청을 sub `"dev"` 한 사용자로 처리하므로 공개 서버에서 쓸 수 없다. 러너의 off 우회는 https가 아닌 로컬 설정(`http://localhost:3500` 등)에서만 가능하고, 공개 설정 `.env`로는 `run_selfplay.py --dev-login`을 쓴다.
- FastAPI 문서 라우트(`/docs`, `/docs/oauth2-redirect`, `/redoc`, `/openapi.json`)를 만들지 않는다(404). 로컬 설정에서는 그대로 있다.

### 속도 제한 버킷 키

로그인된 사용자는 `sub` 기준으로 버킷을 나눈다(`u:{sub}`) — IP 공유 여부와 무관하게 사용자별로 독립이다. `GUARD_AUTH=off`일 때만 클라이언트 IP(`ip:{ip}`)로 대체한다. 클라이언트 IP 자체는 `TRUST_PROXY=true`(`.env`, 기본 `false`)일 때만 `CF-Connecting-IP` 헤더를 쓰고, 그 외에는 `request.client`(uvicorn 기본 프록시 헤더 처리 결과)를 쓴다.

### GuardEvent (이벤트 로그)

허들에 걸릴 때마다 `type: "guard"` 이벤트를 기록한다 — `{layer, reason, ip_hash, user_sub}`. `layer`는 `"auth"`(401)·`"user_daily"`(403)·`"daily_cap"`(503) 3종이다. `ip_hash`는 원문 IP의 SHA-256 앞 12자다. **이 이벤트는 인스펙터(`GET /attempts/{attempt_id}/inspector`)에 노출되지 않는다** — 측정·운영 로그 전용이며, `events` 테이블에는 남지만 세션 소유 attempt와 연결되지 않는 경우가 많다(판 생성 전에 걸리는 401·403·503은 임의 uuid를 session_id로 쓴다).

### 라우트별 가드 매트릭스

| 라우트 | 로그인(`require_user`) | 판 주인(`require_attempt_owner`) | 속도 제한 버킷 |
|---|---|---|---|
| `GET /health` | 불필요 | — | — |
| `/api/v1/auth/*` | 라우트별(아래 개발 계정 절 등) | — | — |
| `POST /sessions` | 필요 | — (남의 `prior_attempt_id`는 무시) | `ip_sessions_per_minute` |
| `POST /sessions/{attempt_id}/loops` | 필요 | 필요 | — |
| `POST /loops/{loop_id}/utterances` | 필요 | 필요 | `ip_actions_per_minute` |
| `POST /loops/{loop_id}/beats/next` | 필요 | 필요 | — |
| `POST /loops/{loop_id}/paw/respond` | 필요 | 필요 | — |
| `GET /loops/{loop_id}/notes` | 필요 | 필요 | — |
| `GET /loops/{loop_id}/observations` | 필요 | 필요 | — |
| `GET /loops/{loop_id}/night/previous` | 필요 | 필요 | — |
| `GET /loops/{loop_id}/npcs` | 필요 | 필요 | — |
| `POST /loops/{loop_id}/night/draft` | 필요 | 필요 | — |
| `PATCH /nights/{night_id}/claims` | 필요 | 필요 | — |
| `POST /nights/{night_id}/submit` | 필요 | 필요 | — |
| `POST /nights/{night_id}/questions` | 필요 | 필요 | `ip_actions_per_minute` |
| `GET /nights/{night_id}/options` | 필요 | 필요 | — |
| `POST /nights/{night_id}/rule` | 필요 | 필요 | — |
| `POST /nights/{night_id}/rule/preview` | 필요 | 필요 | — |
| `GET /attempts/{attempt_id}/journey` | 필요 | 필요 | — |
| `GET /attempts/{attempt_id}/harness` | 필요 | 필요 | — |
| `GET /attempts/{attempt_id}/inspector` | 불필요 | — (별도: 헤더 `X-Inspector-Token` 토큰 인증, 틀리면 403, 토큰 미설정이면 404) | — |

판 하위 경로(`attempt_id`·`loop_id`·`night_id`가 들어간 17개 라우트, 인스펙터 제외)는 읽기 전용 GET까지 전부 로그인과 판 주인 확인을 건다. 속도 제한 버킷은 판 생성(`/sessions`)과 발화·신의 질문(`utterances`, `questions`)에만 추가로 걸린다. 이름은 "IP 버킷"에서 유래했지만 실제 키는 위 "속도 제한 버킷 키" 절을 따른다.

### 판 주인 확인 (F26, 2026-09-17)

- 경로의 `loop_id`·`night_id`는 속한 판으로 거슬러 올라가 확인한다. 주인 비교는 세션 `sub` → `users.id` → `attempts.user_id`다. 같은 개발 계정(sub `dev:{id}`)이면 브라우저·세션이 달라도 같은 판을 쓴다.
- 비로그인은 주인 확인 전에 **401**(`{"detail": "로그인이 필요하다"}`)이 먼저 난다.
- **404** `{"detail": "판을 찾을 수 없다"}` — 남의 판, 없는 판, UUID가 아닌 ID, `user_id`가 없는 구판 모두 같은 응답이다(존재 여부를 흘리지 않는다). 본문 검증(422)·상태 전이(409)보다 먼저 나며, 거부된 요청은 판 상태를 바꾸지 않는다.
- `POST /sessions`의 `prior_attempt_id`가 남의 판이면 없는 판처럼 무시한다(1회차, `prior_cell_results: null`).
- `prior_attempt_id`가 UUID 형식이 아니면(빈 문자열 포함) **422**(FastAPI 기본 검증 에러)이고 판을 만들지 않는다. 형식 검사는 판 존재 여부와 무관해 아무것도 흘리지 않으므로 무시 대신 요청 오류로 돌려준다. 이어하지 않을 때는 필드를 빼거나 `null`로 보낸다.
- `GUARD_AUTH=off`면 모든 요청이 sub `"dev"` 한 사용자로 처리되므로, 그 상태에서 만든 판만 열리고 로그인 사용자의 판은 404다.

### POST /api/v1/auth/dev/login (개발 계정, 2026-09-20까지)

`POST /api/v1/auth/dev/login` `{id, password}` — `DEV_LOGIN=on`일 때만 열린다(아니면 404). 성공 200 `{ok, user}` + `rd_session` 쿠키(구글 로그인과 동일, sub `dev:{id}`). 실패 401 `{"detail":"아이디 또는 비밀번호가 틀렸다"}`, IP당 분당 5회 초과 429(허들 429와 같은 본문), 64자 초과 422. 2026-09-20 제출 뒤 `.env`에서 `DEV_LOGIN`을 빼면 닫힌다(이미 발급된 dev 세션도 함께 무효).

## 타입
CellScores = `{cause: number, motive: number, side_effect: number, identity: number}`

Line = `{kind: "scene"|"action"|"rule_result"|"statement"|"broadcast"|"npc"|"paw_effect"|"fragment"|"system", speaker: string|null, text: string, image_id: string|null, voice_id: string|null, observation_id: string|null}` (2026-09-18, 낮 화면 VN 설계 §3)
- `speaker`: 인물 이름·"관리자"·null. `statement`·`fragment` 줄의 `text`는 `이름: …` 꼴을 그대로 둔다 — 프론트가 그린다.
- `image_id`: 이 줄에서 바꿔 보여 줄 장면 그림(장면 줄은 비트 첫 그림, 행동 줄은 그 행동의 첫 삽화). 없으면 null.
- `voice_id`: 지금은 항상 null — 낮 방송 음원은 프론트 `voiceForLine`이 문구로 고른다.
- `observation_id`: 단서 기록과 연결. `system` 줄만 null.
- 줄 목록은 응답 조립 때 계산하고 저장하지 않는다.

2026-09-08 이후 제출의 side_effect는 저장 호환용 0이다. 화면은 상황(원인·동기 평균)과 정체를 각 100% 기준으로 보여주며 총점 반영 비중은 70:30이다. 기존 제출 기록은 재채점하지 않는다.

## Connected investigation additive contract (2026-09-09)

Existing fields remain unless explicitly corrected below. Empty arrays/null are valid; clients must not manufacture evidence or rule success.

- `Observation = {observation_id: string, attempt_id: string, loop_id: string, loop_n: number, beat: number, scene_id: string, scene_title: string, actor: string|null, text: string, source_kind: "scene"|"image"|"statement"|"rule_result", verification: "observed"|"reported", illustrations: Illustration[], rule_id: string|null}`. An observed statement means it was said, not that its content is true.
- Start-loop and next-beat responses add `observations: Observation[]`; utterance responses also add that field. These are newly disclosed public records. Notes GET adds `observation_ids: string[]` and `sources: Observation[]` to every note. Legacy notes return empty sources rather than invented provenance.
- `GET /loops/{loop_id}/observations` returns `{observations: Observation[]}` for all already disclosed observations in this attempt up to this loop. This is read-only and consumes no game budget.
- `GET /loops/{loop_id}/night/previous` returns `{previous_answer: null | {loop_n: number, free_text: string, claims: string[], tapped_note_ids: number[], draft_text: string}}`. `draft_text` equals the previous submitted night's exact `free_text`, including line breaks and whitespace. `claims` remains the separate confirmed/scored claim list. New attempts return null. Draft POST still accepts optional `inherited_note_ids: number[]` for compatibility. Selected `tapped_note_ids` no longer contribute to claims (2026-09-17): notes are a reference list only. Original free_text and selected IDs remain stored separately.
- Question response adds `status: "supported"|"contradicted"|"unknown"`, `evidence_ids: string[]`, `evidence: Observation[]`, `next_observation: string|null`. Full question, answer and detail persist. Unknown has no confirmed note. Grounding uses original public observations, never hidden truth/user hypotheses/model summaries.
- Each option adds `target: string, action: string, effect: "enforce"|"suppress", when_beat: number|"any", reason: string, evidence_ids: string[], expected_observation: string`. May return 0–3 candidates. If empty, free input/rewrite remains available.
- `POST /nights/{night_id}/rule/preview` request `{custom_text: string}` returns `{preview_id: string, original_text: string, executable: boolean, interpretation: string|null, limitations: string[], alternatives: string[], conflicts: string[], rule: null|{target: string, action: string, effect: "enforce"|"suppress", when_beat: number|"any", label: string}}`. Preview does not apply a rule or end intervention. The client must show original/meaning/limits/conflicts and require an explicit apply click.
- Rule POST accepts `preview_id?: string` with choice custom. Custom apply requires a current successful preview matching exact custom_text; without it returns ok=false with reason. Confirmed apply uses stored preview semantics without remapping. Unsupported alternative is never applied silently.
- Harness GET adds `experiments: [{rule_id: string, intent: string|null, interpretation: string, opportunities: [{loop_n: number, beat: number, condition: string, actual_action: string|null, result: "obeyed"|"violated"|"conflict"|"not_evaluable", observation_ids: string[], side_effect: string|null}]}]` and `metrics: {note_source_linkage: Metric, rule_compliance: Metric, question_grounding: Metric, recommendation_relevance: Metric, custom_semantics: Metric, checker_accuracy: Metric}`. `Metric = {numerator: number|null, denominator: number, value: number|null, reviewed: number, method: string}`. Human semantic/accuracy metrics remain null with reviewed=0 until independently reviewed. No opportunity means denominator=0 and value=null.
- `harness_summary` adds `model_calls: number, model_attempts: number`; `harness_interventions` counts calls with violations/fallback only; `rule_success_rate` is evaluable rule opportunity proportion or null. Tool side effects remain separate from paw-linked effects.

Draft selection clarification: `tapped_note_ids` is the FULL current selection, old retained plus new. Selecting/deselecting a note only changes the reference marks restored next night; it never changes scoring candidates or the player's prose. Night 2 restores night 1's direct writing, night 3 restores night 2's, and so on within the same attempt. Confirm-screen claim edits affect that night's scoring, not the separately saved direct writing. Night UI shows the editable prose first; notes and the observation gallery load only when opened.

Historical coverage correction: `harness_summary.model_calls` and `model_attempts` are nullable; legacy incomplete logs return null and `model_call_coverage: "legacy_partial_or_unavailable"`. Complete new logged calls use `"complete_logged_calls"`. These counts do not claim human checker accuracy. Harness response also includes `measurement_version`.

Next-beat response additionally returns `budget_left: number` (including day_done). It is the current post-scene budget. Monkey-paw wishes never reduce it (F11, 2026-09-17). Frontend consumes it when present for backward compatibility.

Scene failure handling: loop start and next-beat persist scene progress, budget effects, observations and notes atomically. A storage failure rolls those changes back; retry returns the same next scene rather than skipping it. Optional ambient provider failures return the scene with a safe current-record dialogue candidate (or null when no safe candidate exists) and a retained failure audit. Model-call audit records persist separately from public scene records and are never player evidence. A monkey-paw wish already offered in the attempt (accepted or declined) is not offered again; legacy duplicate explanation rules share one actual explanation and carry no budget cost.

Question answers (2026-09-09): `answer` is a short natural-language string, no longer a fixed verdict enum. It may explain the scenario's public surface rules, connect observed events and clearly qualified possibilities, and use the last two question/answer pairs in the current loop for conversational continuity. Hidden truth, hidden cause chains, unrevealed observations and endings are never passed to this model. Prior answers provide conversational context only, not proof.

A successful advisor question uses one structured model call (`advisor_answer`) returning `{question_kind: "proposition"|"lookup", evidence: [{id, quote, relation}], answer: string}`. Answer length is 1–400 characters; evidence contains at most two original public records. Input retrieval chooses at most eight distinct records with at most 6,000 source-text characters by topic, actor, wording and recency, prioritizing explicitly requested loop numbers. Repeated wording in different loops/scenes retains its event scope. Original question wording and complete selected source sentences are preserved. Invalid IDs, non-verbatim quotes and contradictory duplicate assessments trigger bounded repair attempts; provider failures stop without repeated calls. All actual attempts are audited, and one question is charged at most once (unknown answers are refunded within the per-night cap — see the 신의개입 section, 2026-09-18). Capability guidance requires no model call.

HTTP `status` remains a conservative assessment of what the quoted observations establish about the original question, separate from the natural answer's explanation of basic rules or qualified inference. A related citation does not by itself prove a reason, identity, future event or execution of a reported instruction. Unknown metadata does not replace a natural answer with a refusal. `detail` is server-rendered optional source text/limits; the model cannot supply it. Unknown may recover at most two topical partial records when no relevant source was selected. `next_observation` points to a known scene or actor when available. The UI presents the short answer first and puts source cards and inspection guidance under a collapsed disclosure; it does not append the entire notebook to every answer.

Current ambient dialogue and its original statement records are saved as notes in the same scene transaction. Its internal model schema is `{candidate_index: integer|null}`; HTTP ambient stays `{lines:[{code,name,text}]}`. Trusted quotation candidates retain scene/erasure/forbidden-word guards and do not run speculative unknown-person recognition intended for free generation.

## Gameplay clarity and authored dialogue (2026-09-10)

- Loop start adds optional `ambient: {lines:[{code:string,name:string,text:string}]}|null`, same as next-scene. Initial `observations` includes those newly heard lines. UI seeds this dialogue once.
- Ambient speech is authored scenario data selected deterministically from the actual scene, participants and completed action prerequisites. No ambient model call is made. Suppressed actions and absent actors cannot supply their original dialogue. It consumes no player conversation budget. Spoken lines remain `statement`/`reported` observations with source-linked notes and participant memory. First-person explanations produced by information rules are likewise statements, not independently verified facts.
- Scene and action observations remain available in the notebook. Day log uses a short save notice rather than repeating the source text. Pawn-offer refusal identifies the offer explicitly.
- UI labels describe scenes and today's shared conversation budget: six scenes per day,8/7/6/5/4conversations across five days, one per actor per scene. Scene advance/notebook/ambient are free; advance does not replenish the budget. Existing special-rule conversation costs remain. Initial guide is compact with expandable detailed rules and can be reopened during play.
- Custom preview recognizes the player's report-question condition, for example `민석이 보고하는 것을 내가 물어보면 상세하게 설명한다.` It stores canonical action `보고를 물으면 자신이 한 일을 자세히 설명한다` in the existing rule field, with original text preserved in the preview/audit and natural interpretation shown to the player. No migration is required. Currently eligible actors are declared by scenario question-reply data; unsupported actors/conditions are explicitly declined. Conditional requests are not replaced with a generic observation-explanation alternative.
- These rules are excluded from autonomous planning and activate only on a direct report-related question/request to the target. Looking-at/wearing homonyms, room-location questions, explicit topic exclusion and declarative promises do not activate them. A player's own report is not reinterpreted as the NPC's report.
- A triggered report rule selects authored character knowledge using actual current-loop action prerequisites, never future/suppressed actions. This can reveal what the actor personally reported even though an outside observer did not hear it. Responses before a room visit describe preparation/intention. Responses after altered actions use different authored branches. This is deliberate story content, not model-invented evidence. Ordinary direct conversation still uses the configured NPC model.
- `RuleExecutionEvent` records the actual spoken response and its observation ID. Authored fulfilled responses are `obeyed`; unavailable legacy conditional configurations are not self-certified as successful merely because a model produced text.
- Image damage remains a visual layer. Dialogue, inputs, controls and notebooks have no inherited damage transform/filter. Main reading text is18px, supporting text16px, with1.7line height.
