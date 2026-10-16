# 이어하기·마이페이지·회원탈퇴 설계 (2026-10-16)

- 근거: 사용자 요청 2026-10-16. 플레이 도중 창을 닫고 다시 들어오면 지금은 무조건 새 판이 열린다. 진행 중인 판을 이어서 하거나 다시 시작하는 길을 고를 수 있게 하고, 이어하기와 회원탈퇴만 담은 최소 마이페이지를 만든다.
- 검토 등급: 회원탈퇴 **A** (데이터 손실), 이어하기·마이페이지 **B** (게임 흐름·UI)
- 결정: 브레인스토밍 2026-10-16 (사용자 확정 5건 + 컨트롤러 판단 3건, 아래 표)

## 0. 문제

`/play`는 마운트되자마자 `createSession`을 부른다(`frontend/app/play/page.tsx:202-209`). 판 상태는 처음부터 DB에 다 있는데(attempts·loops·npc_states·nights·notes·rules·events), 그것을 다시 불러오는 경로가 없다. 그래서 새로고침이나 창 닫기만으로 진행 중인 판을 잃고, 하루 판 수 한도(5회)도 한 칸 줄어든다.

회원탈퇴 경로도 없다. 처리방침은 "계정 정보는 탈퇴 시 지체 없이 파기"라고 적고 있다.

## 1. 확정한 결정

| 항목 | 결정 | 출처 |
|---|---|---|
| 대상 | 로그인 사용자만. 비로그인 플레이는 없다 | 사용자 |
| 진행 중인 판 수 | 한 사람당 하나 | 사용자 |
| 재진입 화면 | 진행 중인 판이 있으면 "이어하기 / 다시 시작하기" 선택. 다시 시작하기에는 하루 5회에서 1회 차감된다는 안내 | 사용자 |
| 이어하기 정밀도 | 회차(하루) 단위. 그날 낮의 예산·NPC 상태·단서는 유지하고 대화 말풍선은 되살리지 않는다. 밤·채점·개입 단계면 그 단계로 | 사용자 |
| 다시 시작하기 | 기존 판은 `abandoned`로 닫고 새 판을 만든다. 포기한 판은 다시 이어할 수 없다 | 사용자 |
| 마이페이지 | 이어하기 버튼과 회원탈퇴만 둔다 | 사용자 |
| 탈퇴 시 데이터 | 전부 즉시 삭제 | 사용자 |

### 컨트롤러 판단 (되돌릴 수 있음)

1. **"진행 중인 판" = 그 사용자의 가장 최근 `status='active'` 판.** 지금까지는 새 판을 만들어도 이전 판을 닫지 않아 `active` 판이 여러 개 남아 있을 수 있다. 가장 최근 것 하나만 본다. 오래된 `active` 판은 건드리지 않는다.
2. **회차가 하나도 없는 진행 중인 판은 묻지 않고 그대로 쓴다.** 진입 문장만 보고 나간 판에 선택 화면을 띄울 이유가 없고, 새로고침으로 판 수가 줄던 문제가 여기서 풀린다.
3. **다시 시작한 판은 1회차 새 판이다.** `prior_attempt_id`를 넘기지 않으므로 포기한 판의 점수·쿠키를 물려받지 않는다. 이전 판을 이어받는 기존 "다시 도전"(클리어·멸망 뒤 retry)과는 다른 경로다.

## 2. 백엔드

### 2.1 판 상태

`attempts.status`에 `abandoned`를 더한다(`active|closed|abandoned`). 컬럼이 `String(16)`이라 마이그레이션은 없다. `count_today`는 생성 시각만 세므로 포기한 판도 그날 판 수에 그대로 들어간다. 이것이 "다시 시작하면 1회 차감"의 실체다.

### 2.2 `GET /api/v1/me/attempts/active`

`require_user` 뒤에서 사용자의 진행 중인 판을 찾는다. 없으면 `{"attempt": null, "today_remaining": n}`.

있으면 다음을 돌려준다.

```
{
  "attempt": CreateSessionRes 모양 (attempt_id, attempt_n, entry_lines, prior_cell_results),
  "resume_phase": "entry" | "day" | "night" | "score" | "god",
  "loop": StartLoopRes 모양 | null,
  "night": 단계별 밤 데이터 | null,
  "today_remaining": n
}
```

`resume_phase`는 최신 회차 상태로 정한다.

| 최신 회차 `loops.state` | `resume_phase` | 프론트가 여는 화면 |
|---|---|---|
| (회차 없음) | `entry` | 진입 화면 (선택 화면 없이) |
| `day` | `day` | 낮 화면, 현재 비트 장면부터 |
| `night_pending`, `night_draft` | `night` | 밤 답안 작성 |
| `scored` | `score` | 채점 결과 |
| `intervention` | `god` | 신의 개입 |
| `closed` | `entry` | 다음 날을 시작하는 진입 흐름 |

**낮 화면 복원.** `loop`는 `start_loop`가 돌려주는 `StartLoopRes`와 같은 모양으로 만든다. 현재 비트 장면은 `execute_scene`과 `_scene_lines`를 다시 불러 그린다. `execute_scene`은 이미 기록된 규칙 실행(`rule_execution` 이벤트)과 공개된 관찰을 읽어 중복을 거르고, `on_action`은 관찰이 처음 생길 때만 부른다. 그래서 같은 비트를 다시 그려도 세계 효과나 이벤트가 두 번 생기지 않는다고 본다. 이 멱등성은 구현 계획의 첫 테스트로 확인한다. 깨지면 쓰기 없는 읽기 전용 경로를 따로 만든다.

`budget_left`·`active_rules`·`observations`는 DB 값을 그대로 쓴다. `ambient`(첫 장면 무료 대화)와 `aftermath`는 되살리지 않고 `null`로 둔다.

**밤·채점·개입 복원.** 각 단계 화면이 이미 부르는 조회 API(`/night/previous`, `/nights/{id}/options` 등)와 `nights` 행, `answer_scored` 이벤트로 그 화면이 처음 받는 데이터를 만든다. 정확한 필드는 구현 계획에서 각 화면의 props를 기준으로 맞춘다.

### 2.3 `POST /api/v1/me/attempts/active/abandon`

진행 중인 판을 `abandoned`로 바꾸고 `204`를 돌려준다. 진행 중인 판이 없으면 아무 일도 하지 않고 `204`. 프론트는 이어서 기존 `POST /sessions`를 부른다. 한도에 걸리면 기존 가드 화면(`daily_limit`)이 그대로 뜬다.

### 2.4 `DELETE /api/v1/auth/me` (회원탈퇴)

로그인 세션 쿠키의 사용자 한 명의 데이터를 **한 트랜잭션에서** 지우고 세션 쿠키를 삭제한다. FK에 `ON DELETE CASCADE`가 없으므로 자식부터 지운다.

1. 그 사용자의 attempt id 목록을 구한다(`attempts.user_id`).
2. `nights` → `npc_states` → `loops` → `notes` / `rules` → `survey_votes`(user_id) → `events`(session_id ∈ attempt ids) → `attempts`
3. `events` 중 `type='guard'` 이고 `payload->>'user_sub'`가 이 사용자의 Google sub인 행
4. `users` 행

응답은 `204`와 세션 쿠키 삭제. 이미 지워진 사용자(쿠키는 유효한데 users 행이 없음)도 `204`.

**검증 기준:** 두 사용자의 데이터를 만들어 한 명을 탈퇴시킨 뒤, 탈퇴한 사용자의 행이 모든 테이블에서 0개이고 다른 사용자의 행 수는 그대로인지 확인한다.

### 2.5 배치

- 엔드포인트: `auth_router.py`에 `DELETE /me`, 새 `me_router.py`에 `/me/attempts/active`·`/abandon`. 기존 판 라우트와 같은 가드(`require_user`)를 쓴다.
- 판정·조립 로직: 유스케이스(interactor) 한 곳. 라우터에는 넣지 않는다.
- 삭제: `UserRepository.delete_with_data(user_id, sub)` 하나에 순서를 모은다. 저장소 관행대로 기존 `game_repository.py`·`user_repository.py`에 넣고 새 파일을 늘리지 않는다.
- 판 소유 라우트 인벤토리 테스트가 있으므로 새 라우트를 거기에도 올린다.

## 3. 프론트엔드

### 3.1 `/play` 진입

마운트 시 `getActiveAttempt()`를 먼저 부른다.

| 응답 | 동작 |
|---|---|
| `attempt: null` | 지금처럼 `createSession` |
| `resume_phase: "entry"`이고 회차 없음 | 그 판을 그대로 `attempt`로 쓰고 진입 화면 |
| 그 밖 | **선택 화면** |
| `?resume=1`로 들어옴 | 선택 화면 없이 바로 이어하기 |

선택 화면은 진입 화면과 같은 배경과 버튼 스타일을 쓴다.

- **이어하기** → 응답의 `loop`·`night`로 state를 채우고 `resume_phase`에 맞는 단계로 간다.
- **다시 시작하기** → 아래에 "오늘 남은 판 {today_remaining}/5 · 다시 시작하면 1회가 차감됩니다" 안내. 누르면 `abandon` 후 `createSession`. `today_remaining`이 0이면 버튼을 끄고 "오늘은 더 시작할 수 없습니다"를 보인다.

### 3.2 `/mypage`

- 진입 시 `getMe()`. 401이면 랜딩(`/`)으로 보낸다.
- `getActiveAttempt()`로 진행 중인 판이 있을 때만 **이어하기**(`/play?resume=1`).
- **회원탈퇴** → 브라우저 `confirm()`을 쓰지 않고 같은 화면에 확인 단계를 펼친다. "모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다" + "탈퇴" / "취소". 탈퇴하면 `DELETE /auth/me` 후 `/`로 간다.
- 그 밖의 정보(이메일·기록·통계)는 두지 않는다.

### 3.3 랜딩

로그인 상태면 "로그아웃" 위에 **마이페이지** 버튼을 더한다. 페이드인 지연은 기존 버튼 순서에 맞춘다.

## 4. 테스트

- 백엔드 pytest
  - `execute_scene`을 같은 비트에 두 번 불러도 이벤트·관찰·세계 효과가 늘지 않는다 (멱등성 전제 확인, 가장 먼저)
  - 회차 상태별 `resume_phase` 매핑 6가지
  - 포기한 판은 진행 중인 판으로 잡히지 않고, 그날 판 수에는 남는다
  - 남의 판은 진행 중인 판으로 잡히지 않는다
  - 탈퇴: 탈퇴한 사용자의 행 0개, 다른 사용자의 행 그대로, 세션 쿠키 삭제
  - 새 라우트의 비로그인 401
- 헤드리스 Playwright (`frontend/tests/*.cjs`, `headless: true`)
  - 진행 중인 판이 있을 때 선택 화면과 차감 안내가 뜬다
  - 이어하기를 누르면 낮 화면으로 간다
  - 마이페이지 탈퇴 확인 단계
- `npx tsc --noEmit`, 백엔드 전체 테스트

## 5. 범위 밖

- 대화 말풍선·열려 있던 팝업 복원 (회차 단위로 결정)
- 오래된 `active` 판 일괄 정리
- 탈퇴 후 같은 Google 계정 재가입 시 그날 판 수 한도가 다시 채워지는 문제
- 마이페이지의 계정 정보·지난 판 기록·통계
