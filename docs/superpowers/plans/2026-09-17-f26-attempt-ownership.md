# F26 판 소유자 확인 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**검토 등급:** A (인증·비용)

**Goal:** 판(attempt)에 속한 모든 게임 API에서 "로그인 사용자 = 판 주인"을 확인하고, 판 내용 조회 API에도 로그인을 요구한다.

**Architecture:** 소유 판정 규칙은 `AttemptRepository.get_owned(attempt_id, user_id)` 한 곳에 둔다. `AttemptAccessInteractor`가 경로 ID 종류별 해석기 표(attempt_id / loop_id→attempt / night_id→loop→attempt)로 판을 찾아 그 규칙에 맞춘다. 인바운드 어댑터에서는 FastAPI 의존성 `guards.require_attempt_owner` 하나가 이 일을 맡고, 판 하위 라우트를 `owned` 서브 라우터에 모아 라우터 단위 의존성으로 강제한다(호출부마다 if를 두지 않는다). 새 라우트를 `owned`에 달고 ID를 빠뜨리면 거부된다(fail-closed).

**Tech Stack:** FastAPI + SQLAlchemy, pytest(`tests/engine`, 실 Postgres 테스트 DB).

## Global Constraints

- 주인 비교 기준은 세션 생성과 같다: `users.get_by_sub(session.sub).id == attempts.user_id`. 구글 계정·개발 계정(`dev:{id}`)·`GUARD_AUTH=off`(`dev`) 모두 같은 식으로 판정한다. 개발 계정은 sub가 같으므로 다른 브라우저·세션에서도 같은 판에 이어 들어갈 수 있다.
- 남의 판·없는 판·잘못된 ID는 모두 **404** `판을 찾을 수 없다`로 같게 응답한다(존재 여부를 흘리지 않는다).
- 비로그인은 기존대로 401(`require_user`가 먼저 돈다).
- 인스펙터(`/attempts/{id}/inspector?token=`)는 토큰 인증만 유지한다(개발자 도구, 로그인 없음).
- DEV_LOGIN 경로는 건드리지 않는다.
- 테스트 실행: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests` (기준 634 passed / 1 failed `test_user_daily_limit_is_five` / 1 xfailed).
- 커밋·푸시·서버 재기동 금지.

## 엔드포인트 전수 표

| 메서드·경로 | 기존 보호 | 변경 후 |
|---|---|---|
| POST `/sessions` | 로그인 | 로그인 + 남의 `prior_attempt_id`는 없는 판처럼 무시 |
| POST `/sessions/{attempt_id}/loops` | 로그인 | 로그인 + 주인 |
| POST `/loops/{loop_id}/utterances` | 로그인 | 로그인 + 주인 |
| POST `/loops/{loop_id}/beats/next` | 로그인 | 로그인 + 주인 |
| POST `/loops/{loop_id}/paw/respond` | 로그인 | 로그인 + 주인 |
| GET `/loops/{loop_id}/notes` | 없음 | 로그인 + 주인 |
| GET `/loops/{loop_id}/observations` | 없음 | 로그인 + 주인 |
| GET `/loops/{loop_id}/night/previous` | 없음 | 로그인 + 주인 |
| GET `/loops/{loop_id}/npcs` | 없음 | 로그인 + 주인 |
| POST `/loops/{loop_id}/night/draft` | 로그인 | 로그인 + 주인 |
| PATCH `/nights/{night_id}/claims` | 로그인 | 로그인 + 주인 |
| POST `/nights/{night_id}/submit` | 로그인 | 로그인 + 주인 |
| POST `/nights/{night_id}/questions` | 로그인 | 로그인 + 주인 |
| GET `/nights/{night_id}/options` | 없음(모델 호출 가능) | 로그인 + 주인 |
| POST `/nights/{night_id}/rule` | 로그인 | 로그인 + 주인 |
| POST `/nights/{night_id}/rule/preview` | 로그인 | 로그인 + 주인 |
| GET `/attempts/{attempt_id}/journey` | 없음 | 로그인 + 주인 |
| GET `/attempts/{attempt_id}/harness` | 없음 | 로그인 + 주인 |
| GET `/attempts/{attempt_id}/inspector` | 토큰 | 토큰(변경 없음) |
| `/health`, `/api/v1/auth/*` | — | 변경 없음 |

---

### Task 1: 소유 판정 — 저장소·유스케이스

**Files:** `backend/apps/engine/adapter/outbound/repositories/game_repository.py`, `backend/apps/engine/app/use_cases/attempt_access_interactor.py`(신규), `backend/tests/engine/test_attempt_ownership.py`(신규)

- [x] 실패 테스트: 주인이면 통과, 남의 판·없는 판·`user_id` 없는 구판·잘못된 UUID·users 행 없는 세션·해석기 없는 경로는 `AttemptNotFound`. loop_id·night_id가 판으로 해석된다.
- [x] `AttemptRepository.get_owned` + `AttemptAccessInteractor.ensure_owner(path_ids, user)` 구현 → 통과.

### Task 2: 라우터 강제 — 의존성·owned 서브 라우터

**Files:** `backend/apps/engine/adapter/inbound/api/v1/guards.py`, `backend/apps/engine/adapter/inbound/api/v1/game_router.py`, `backend/apps/engine/dependencies/engine_dependency.py`, `backend/tests/engine/test_attempt_ownership.py`

- [x] 실패 테스트(HTTP, 전수 파라미터화): 사용자 A의 판·회차·밤 ID로 B가 부르면 404, 비로그인은 401, 인스펙터는 비로그인 + 토큰으로 계속 동작, 라우트 표 검사(판 ID 경로는 인스펙터 외 전부 `require_attempt_owner` 보유).
- [x] `get_attempt_access` 배선, `require_attempt_owner` 의존성, 판 하위 라우트를 `owned` 라우터로 옮김 → 통과. 기존 e2e(주인 정상 흐름) 통과 확인.
- [x] 의존성이 본문 검증보다 먼저 돌므로, 없는 UUID로 본문 상한(422)을 보던 `tests/engine/test_guards.py` 5건은 내 회차·밤 ID를 쓰도록 바꾼다(검사 의도는 그대로).

### Task 3: 이어하기(prior)·예외 경로

**Files:** `backend/apps/engine/app/use_cases/session_interactor.py`, `backend/tests/engine/test_attempt_ownership.py`

- [x] 실패 테스트: B가 A의 판을 `prior_attempt_id`로 넘기면 새 판은 1회차·`prior_cell_results` null(A의 점수가 새지 않음). 개발 계정 세션 두 개(같은 `dev:{id}`)가 같은 판을 이어 씀. `GUARD_AUTH=off`에서 만든 판은 off 상태에서 계속 접근되지만 로그인 사용자의 판은 404.
- [x] `SessionInteractor.start`의 prior 조회를 `get_owned`로 교체 → 통과.

### Task 4: 전체 검증

- [x] `PYTHONPATH=. .venv/bin/pytest -q tests` — 기준 대비 신규 테스트만 늘고 실패는 기존 1건.
- [x] `frontend/contracts/api.ts`는 이미 모든 요청에 `credentials: "include"` — 변경 없음(tsc 불필요).

### 최종 리뷰 반영 (수정 1회)

- [x] I-1 `docs/spec/api_contract.md` 가드 매트릭스에 판 주인 열, 판 주인 확인 절(401 먼저·404 동일 응답·남의 prior 무시), `attempts.user_id`=`users.id` 정정.
- [x] M-1 라우트 표 테스트를 공개 허용 목록 기준 역검사로(앱 실제 라우트 전부, 스키마 숨김·문서 라우트 포함 + 허용 목록 실재). 변이 시험 4종 실패 확인 후 되돌림.
- [x] M-2 비주인 404 전수 테스트에 주인 판 이벤트 수·회차(state·beat·budget_left)·밤·판 상태 불변 단언.
- [x] M-3 `ensure_owner`가 판 ID 없는 경로를 users 조회 전에 거부. `require_attempt_owner`의 `access` 타입 표기.
- [x] M-4 `docs/demo_guide.md` 하네스 페이지는 판을 만든 계정으로 로그인한 브라우저에서 열 것.
- 미반영(별도 2b): M-5 속도 제한 순서, GUARD_AUTH=off 기동 차단, 인스펙터 토큰, /docs 공개, 잘못된 prior_attempt_id 500.
