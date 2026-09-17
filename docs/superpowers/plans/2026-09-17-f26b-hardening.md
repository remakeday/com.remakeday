# F26b 후속 보안 강화 Implementation Plan

**검토 등급:** A (인증·보안)

**Goal:** 공개 배포(api.remakeday.com)에서 인증 우회(`GUARD_AUTH=off`)·인스펙터 토큰 노출·API 문서 노출을 막고, `POST /sessions`의 잘못된 `prior_attempt_id`가 500이 되지 않게 한다.

**Architecture:** "공개 배포인가"는 `Settings.public_deploy` 한 곳에서만 판정한다(`FRONTEND_BASE_URL`이 `https://`면 공개 — 세션 쿠키 `Secure` 판정과 같은 기준). `main.py`의 `deploy_profile(settings)`가 그 값으로 `LocalProfile`/`PublicProfile` 중 하나를 고르고(분기는 여기 한 번), 프로파일 객체가 FastAPI 문서 라우트 설정과 기동 검사를 각자 안다. 기동 검사는 기존 `SESSION_SECRET` 검사와 같이 lifespan에서 `RuntimeError`.

**Tech Stack:** FastAPI + pydantic-settings, pytest(`tests/engine`), Next.js(`frontend/contracts/api.ts`, 인스펙터 페이지).

## Global Constraints

- DEV_LOGIN 경로·F26 판 주인 확인은 건드리지 않는다.
- `.env` 값은 출력·문서·테스트에 적지 않는다. 테스트는 `tests/conftest.py`에서 테스트 전용 값(`INSPECTOR_TOKEN`, 로컬 `FRONTEND_BASE_URL`)을 주입해 `.env`와 무관하게 돈다.
- 테스트: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests` (기준 690 passed / 1 failed `test_user_daily_limit_is_five` / 1 xfailed). 프론트: `cd frontend && npx tsc --noEmit`.
- 커밋·푸시·서버 재기동 금지.

### Task 1: 공개 배포에서 `GUARD_AUTH=off` 기동 거부

**Files:** `backend/core/matrix/grid_keymaker_secret_manager.py`, `backend/main.py`, `backend/tests/engine/test_guards.py`, `backend/tests/conftest.py`

- [x] 실패 테스트: https 프론트 + off → lifespan `RuntimeError("GUARD_AUTH")`; https + on → 기동; localhost + off → 기동.
- [x] `Settings.public_deploy` + `deploy_profile()`(Local/Public) + lifespan에서 `check_startup` → 통과.
- [x] `run_selfplay.py`의 401 안내 문구: `GUARD_AUTH=off`는 로컬 설정에서만 기동된다는 점 반영.

### Task 2: 운영 설정에서 `/docs`·`/redoc`·`/openapi.json` 끄기

**Files:** `backend/main.py`, `backend/tests/engine/test_attempt_ownership.py`

- [x] 실패 테스트: 공개 설정으로 `main`을 새 프로세스에서 import하면 문서 라우트 4개(`/docs`, `/docs/oauth2-redirect`, `/redoc`, `/openapi.json`)가 없다. 개발 설정 기준 `PUBLIC_ROUTES` 검사는 그대로.
- [x] `FastAPI(..., **profile.docs_routes)` → 통과.

### Task 3: 인스펙터 토큰 정리

**Files:** `grid_keymaker_secret_manager.py`(기본값 `""`), `inspector_interactor.py`(`InspectorDisabled`, `hmac.compare_digest`), `game_router.py`(헤더 `X-Inspector-Token`, 비활성 404), `scripts/run_paw_eval.py`, `frontend/contracts/api.ts`, `frontend/app/inspector/[attemptId]/page.tsx`, 테스트(`test_attempt_ownership.py`, `test_e2e_flow.py`), 문서(`docs/demo_guide.md`, `docs/spec/api_contract.md`)

- [x] 실패 테스트: 토큰 미설정이면 맞는 헤더를 줘도 404; 설정 시 헤더 일치 200, 불일치·누락 403; 쿼리 `?token=`은 더 이상 통하지 않음(403); 비교가 `hmac.compare_digest`를 거친다.
- [x] 구현 → 통과. 쿼리 호환은 남기지 않는다(URL은 cloudflared·uvicorn 접근 로그·브라우저 기록에 남는다). 프론트 인스펙터 페이지도 URL `?token=` 자동 조회를 없애고 입력칸만 쓴다.

### Task 4: `prior_attempt_id` 형식 오류 → 422

**Files:** `game_router.py`(`SessionReq.prior_attempt_id: uuid.UUID | None`), `test_attempt_ownership.py`, `docs/spec/api_contract.md`

- [x] 실패 테스트: `{"prior_attempt_id": "not-a-uuid"}` → 422(현재 500), 판이 생기지 않음.
- [x] 타입 변경 → 통과. 프론트는 서버가 준 `attempt_id`(UUID 문자열)만 보낸다.

### Task 5: 전체 검증

- [x] 백엔드 전체 테스트, `npx tsc --noEmit`, 옛 기본 토큰 문자열 grep 0건(문서 기록 제외).

## 결과 (2026-09-17)

- 백엔드 전체 702 passed / 1 failed(기존 `test_user_daily_limit_is_five`) / 1 xfailed — 기준 690 대비 신규 12건. `npx tsc --noEmit` 통과.
- 변이 확인: `PublicProfile.docs_routes`를 비우면 `test_public_deploy_has_no_api_docs_routes`가 실패한다.
- 러너 영향: `run_core_selection.py` Stage 4는 `.env`를 읽는 `scripts.loop_app`(= `main.app`)을 띄운다. https `.env`에서 off로 돌리려면 러너 프로세스에 `GUARD_AUTH=off FRONTEND_BASE_URL=http://localhost:3500`을 함께 준다(환경변수가 `.env`보다 우선). `run_selfplay.py`는 `--dev-login` 사용.

## 최종 리뷰 반영 (수정 1회, 2026-09-17)

cloudflared가 상시 `api.remakeday.com → 127.0.0.1:8500`에 붙어 있어 "공개되지 않은 로컬 설정"이 없다. `.env` 프론트 주소가 localhost거나 비면 `public_deploy`가 거짓이 되어 off 기동이 통과하므로, 기동 검사 외에 요청 기준 방어를 더했다.

- [x] **I-1 요청 기준 방어** — `guards.require_user`의 off 분기: `CF-Connecting-IP` 헤더가 있으면 **403** + `GuardEvent(layer="auth", reason="guard_auth_off_via_proxy")`. 판 경로는 전부 `require_user`를 탄다(`POST /sessions` 직접, `owned` 라우터는 `require_attempt_owner` → `require_user`, `ip_bucket`도 `require_user`에 의존). off 설정의 영향을 받지 않는 인스펙터(토큰)·auth·health만 안 타므로 미들웨어는 두지 않았다. 401은 프론트가 로그인 화면으로 보내는데 off에서는 로그인이 소용없어 오해를 부르고, `code` 없는 403은 GuardScreen 매핑(`daily_attempt_limit`만)에 걸리지 않고 일반 실패로 보인다. 쿠키 `Secure`·`public_deploy`는 그대로.
- [x] **I-1 문서·안내** — `api_contract.md` 허들 절 첫 문단, `run_selfplay.py` 401 안내: `--dev-login` 사용, off는 8500이 아닌 포트의 러너 프로세스 환경변수로만, Cloudflare 경유 요청은 off에서도 거부.
- [x] **M-1** — 인스펙터 토큰 입력칸 `type="password" autoComplete="off" spellCheck={false}`.
- [x] **M-2** — `demo_guide.md` 개발자 뷰: https 프론트 주소 `.env`에서는 `localhost:8500/docs`도 404.
- [x] **후속 4** — `Settings.auth_required`(`guard_auth != "off"`) 한 곳에서 판정하고 `require_user`·`ip_bucket`·`PublicProfile.check_startup`·lifespan `SESSION_SECRET` 검사가 모두 이 값을 쓴다. 전에는 lifespan만 `== "on"`이라 `On`이면 인증은 켜진 채 기본 시크릿 검사를 건너뛰었다.
- [x] **후속 2** — `tests/conftest.py`가 `USER_DAILY_ATTEMPTS`·`DAILY_ATTEMPT_CAP`를 `Settings.model_fields` 기본값으로 환경변수에 고정(`.env`는 그대로).
- 반영 안 함: M-3(프로파일 추상 부모), 후속 1(`run_core_selection.py` Stage 4는 `.env`를 읽는 `main.app`을 띄우므로 러너 프로세스에 `GUARD_AUTH=off FRONTEND_BASE_URL=http://localhost:3500`과 8500이 아닌 포트를 줄 것 — 러너 요청은 헤더가 없어 통과), 후속 3(TRUST_PROXY — 제출 전환 체크리스트), 후속 5(인스펙터 실패 이벤트).
- 테스트(`test_guards.py`): off+CF 헤더 403·`code` 없음, on+CF 헤더 영향 없음, off+CF 거부 시 GuardEvent 기록, `guard_auth="On"` + 기본 시크릿 기동 거부. 기존 off+헤더 없음 통과 테스트 유지. 가짜 설정 객체 2곳(`test_guards._app`, `test_dev_login._client`)에 `auth_required` 추가.
- 결과: 백엔드 747 passed / 0 failed / 1 xfailed(기존 실패 `test_user_daily_limit_is_five` 해소, 밤 작업 테스트 포함), `npx tsc --noEmit` 통과.
