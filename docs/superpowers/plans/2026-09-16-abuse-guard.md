# 과잉 사용 방지 허들 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 외부 API(Anthropic·Gemini) 전환 전에, 판 생성·발화·질문 경로를 로그인 필수 + 사용자 하루 5판 + IP 속도 제한 + 전역 일일 차단기 + 텍스트 길이 상한으로 막는다.

**Architecture:** FastAPI 의존성 3개(`require_user`, `ip_bucket(name, per_minute)`, `daily_guard`)를 게임 라우터에 붙인다. 상태는 DB 집계(사용자 하루 판 수, 전역 하루 판 수)와 프로세스 내 토큰 버킷(IP)만 쓴다. `attempts.user_id` 컬럼 1개 추가(마이그레이션 1). 프런트는 401/403/503 응답 코드를 각각 로그인 안내·하루 한도·정원 마감 화면으로 매핑한다.

**Tech Stack:** FastAPI 의존성, SQLAlchemy + Alembic, pydantic-settings, Playwright 헤드리스.

**Spec:** `docs/superpowers/specs/2026-09-16-abuse-guard-design.md`

## Global Constraints

- 401: 로그인 필요. 403 + `{"code": "daily_attempt_limit"}`: 하루 5판 초과. 429 + `{"detail", "retry_after"}`: IP 속도 제한. 503 + `{"code": "daily_cap"}`: 전역 일일 정원.
- 사용자 하루 한도 **5판**, IP 분당 판 생성 5회·발화·질문 30회, 전역 하루 판 기본 **200**(`DAILY_ATTEMPT_CAP`). 하루 경계는 KST 자정.
- 발화·질문 텍스트 200자 상한. 초과는 FastAPI 검증 422(스펙의 400을 422로 확정 — 기존 검증 오류 경로와 통일).
- 진행 중인 판(발화·비트·밤)은 전역 정원과 무관하게 계속된다. 정원은 **판 생성만** 막는다.
- 원문 IP를 저장하지 않는다. `guard_event`에는 sha256 앞 12자만.
- 테스트: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests`(기준 545 passed). 프런트 `npx tsc --noEmit`, 헤드리스는 한 번에 하나. 서버 재기동 금지(세션 주인이 한다). 커밋은 사용자 지시 뒤 머지 시점.
- 기존 UI 테스트(`frontend/tests/*.cjs`)는 모의 백엔드를 쓰므로 로그인 없이 동작한다. 실서버 셀프플레이 러너(`backend/scripts/run_selfplay.py`)는 세션 쿠키가 필요해진다 → Task 6에서 `--session-cookie` 옵션 또는 `.env` `GUARD_AUTH=off` 스위치로 처리.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `backend/apps/engine/adapter/inbound/api/v1/guards.py` (신규) | `require_user`, `ip_bucket`, `client_ip`, `daily_guard` 의존성 |
| `backend/apps/engine/domain/entities/guard_rules.py` (신규) | 순수: 토큰 버킷 계산, KST 하루 경계, 한도 판정 |
| `backend/apps/engine/adapter/outbound/orms/game_state_orm.py` | `AttemptOrm.user_id` |
| `backend/alembic/versions/2026_09_16_1700-<rev>_attempts_user_id.py` (신규) | 컬럼 추가 |
| `backend/apps/engine/adapter/outbound/repositories/game_repository.py` | `AttemptRepository.create(prior, user_id)`, `count_today(user_id)`, `count_today_all()` |
| `backend/apps/engine/app/use_cases/session_interactor.py` | `start(prior_attempt_id, user_id)`, 한도·정원 판정 호출 |
| `backend/apps/engine/adapter/inbound/api/v1/game_router.py` | 의존성 부착, 텍스트 길이 `Field(max_length=200)` |
| `backend/apps/engine/app/dtos/event_log_dto.py` | `GuardEvent` |
| `backend/core/matrix/grid_keymaker_secret_manager.py` | `guard_auth`, `daily_attempt_cap`, `ip_sessions_per_minute`, `ip_actions_per_minute`, `user_daily_attempts` |
| `backend/tests/pure/test_guard_rules.py`, `backend/tests/engine/test_guards.py` (신규) | 테스트 |
| `frontend/contracts/api.ts`, `frontend/app/play/page.tsx`, `frontend/components/screens/GuardScreen.tsx` (신규) | 코드별 화면 |
| `frontend/tests/guard.cjs` (신규) | 401/403/503 화면 헤드리스 |
| `backend/scripts/run_selfplay.py` | 쿠키 옵션 |
| `docs/spec/api_contract.md`, `docs/HANDOFF-26-09-16.md` | 문서 |

---

### Task 1: 순수 규칙 — 토큰 버킷·KST 하루 경계·한도 판정

**Files:**
- Create: `backend/apps/engine/domain/entities/guard_rules.py`
- Test: `backend/tests/pure/test_guard_rules.py`

**Interfaces:**
- `kst_day_start(now: datetime) -> datetime` — `now`(tz-aware UTC)를 KST 자정(UTC 기준 15:00 전날)으로 내림
- `class TokenBucket(capacity: int, refill_per_sec: float)`; `.take(key: str, now: float) -> tuple[bool, float]` — (허용 여부, 다음 허용까지 초)
- `attempts_allowed(count_today: int, limit: int) -> bool`

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/pure/test_guard_rules.py
from datetime import datetime, timezone, timedelta
from apps.engine.domain.entities.guard_rules import kst_day_start, TokenBucket, attempts_allowed


def test_kst_day_start_rolls_at_kst_midnight():
    # 2026-09-16 14:59 UTC = 09-16 23:59 KST → 09-16 00:00 KST = 09-15 15:00 UTC
    now = datetime(2026, 9, 16, 14, 59, tzinfo=timezone.utc)
    assert kst_day_start(now) == datetime(2026, 9, 15, 15, 0, tzinfo=timezone.utc)
    # 15:00 UTC = 09-17 00:00 KST → 새 날
    assert kst_day_start(now + timedelta(minutes=1)) == datetime(2026, 9, 16, 15, 0, tzinfo=timezone.utc)


def test_token_bucket_allows_capacity_then_blocks_and_refills():
    bucket = TokenBucket(capacity=2, refill_per_sec=1.0)
    assert bucket.take("ip", now=0.0) == (True, 0.0)
    assert bucket.take("ip", now=0.0) == (True, 0.0)
    ok, wait = bucket.take("ip", now=0.0)
    assert ok is False and 0.9 <= wait <= 1.0
    assert bucket.take("ip", now=1.0)[0] is True
    assert bucket.take("other", now=1.0)[0] is True  # 키별 독립


def test_attempts_allowed():
    assert attempts_allowed(4, 5) and not attempts_allowed(5, 5)
```

- [ ] **Step 2: 실패 확인** — `PYTHONPATH=. .venv/bin/pytest -q tests/pure/test_guard_rules.py` → ModuleNotFoundError
- [ ] **Step 3: 구현**

```python
# backend/apps/engine/domain/entities/guard_rules.py
"""과잉 사용 방지 — 순수 규칙 (토큰 버킷·KST 하루·한도). I/O 없음."""

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def kst_day_start(now: datetime) -> datetime:
    local = now.astimezone(KST)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(timezone.utc)


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self._capacity = capacity
        self._refill = refill_per_sec
        self._state: dict[str, tuple[float, float]] = {}  # key -> (tokens, last)

    def take(self, key: str, now: float) -> tuple[bool, float]:
        tokens, last = self._state.get(key, (float(self._capacity), now))
        tokens = min(self._capacity, tokens + (now - last) * self._refill)
        if tokens >= 1.0:
            self._state[key] = (tokens - 1.0, now)
            return True, 0.0
        self._state[key] = (tokens, now)
        return False, (1.0 - tokens) / self._refill


def attempts_allowed(count_today: int, limit: int) -> bool:
    return count_today < limit
```

- [ ] **Step 4: 통과 확인** — 3 passed

---

### Task 2: 설정·`attempts.user_id`·저장소 집계

**Files:**
- Modify: `backend/core/matrix/grid_keymaker_secret_manager.py` (Settings), `backend/apps/engine/adapter/outbound/orms/game_state_orm.py:24-36` (`AttemptOrm`), `backend/apps/engine/adapter/outbound/repositories/game_repository.py:27-36` (`AttemptRepository`)
- Create: Alembic revision `attempts_user_id` (`alembic revision -m "attempts_user_id"` 후 편집; down_revision은 현재 head `64a6b77faeb0`을 `alembic heads`로 확인)
- Test: `backend/tests/engine/test_guards.py`

**Interfaces:**
- Settings: `guard_auth: str = "on"`, `user_daily_attempts: int = 5`, `daily_attempt_cap: int = 200`, `ip_sessions_per_minute: int = 5`, `ip_actions_per_minute: int = 30`
- `AttemptOrm.user_id: Mapped[uuid.UUID | None]` (nullable, index)
- `AttemptRepository.create(prior, user_id: uuid.UUID | None = None)`, `count_today(user_id, now) -> int`, `count_today_all(now) -> int` — `created_at >= kst_day_start(now)`

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/engine/test_guards.py
import uuid
from datetime import datetime, timezone, timedelta
from apps.engine.adapter.outbound.repositories.game_repository import AttemptRepository


def test_attempt_counts_by_user_and_day(db_session):
    repo = AttemptRepository(db_session)
    u1, u2 = uuid.uuid4(), uuid.uuid4()
    for _ in range(3):
        repo.create(None, user_id=u1)
    repo.create(None, user_id=u2)
    repo.create(None)  # 익명(구버전) 판
    now = datetime.now(timezone.utc)
    assert repo.count_today(u1, now) == 3
    assert repo.count_today(u2, now) == 1
    assert repo.count_today_all(now) == 5
    # 어제 판은 세지 않는다
    old = repo.create(None, user_id=u1)
    old.created_at = now - timedelta(days=2)
    db_session.commit()
    assert repo.count_today(u1, now) == 3
```

- [ ] **Step 2: 실패 확인** — TypeError(user_id) / AttributeError(count_today)
- [ ] **Step 3: 구현**

`AttemptOrm`에 `user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)` 추가. 마이그레이션:

```python
def upgrade() -> None:
    op.add_column("attempts", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])

def downgrade() -> None:
    op.drop_index("ix_attempts_user_id", table_name="attempts")
    op.drop_column("attempts", "user_id")
```

`AttemptRepository`:

```python
    def create(self, prior: AttemptOrm | None, user_id: uuid.UUID | None = None) -> AttemptOrm:
        row = AttemptOrm(
            attempt_n=(prior.attempt_n + 1) if prior else 1,
            prior_attempt_id=prior.id if prior else None,
            prior_cell_results=prior.prior_cell_results if prior else None,
            cookies_seen=list(prior.cookies_seen or []) if prior else [],
            user_id=user_id,
        )
        ...

    def count_today(self, user_id: uuid.UUID, now: datetime) -> int:
        start = kst_day_start(now)
        return self._s.query(AttemptOrm).filter(AttemptOrm.user_id == user_id, AttemptOrm.created_at >= start).count()

    def count_today_all(self, now: datetime) -> int:
        start = kst_day_start(now)
        return self._s.query(AttemptOrm).filter(AttemptOrm.created_at >= start).count()
```

Settings 필드 5개 추가. 테스트 DB(`pigfarm_test`)는 conftest가 스키마를 만드는 방식을 확인(`grep -n "create_all\|alembic" tests/conftest.py`)해 컬럼이 반영되게 한다.

- [ ] **Step 4: 통과 확인** — 전체 스위트 green(`create` 시그니처 기본값으로 기존 호출 무변경)

---

### Task 3: 의존성 3종과 `GuardEvent`

**Files:**
- Create: `backend/apps/engine/adapter/inbound/api/v1/guards.py`
- Modify: `backend/apps/engine/app/dtos/event_log_dto.py` (`GuardEvent`, `EventType.GUARD`)
- Test: `backend/tests/engine/test_guards.py`

**Interfaces:**
- `client_ip(request) -> str` — `X-Forwarded-For` 첫 값(있으면) 아니면 `request.client.host` (09-17 대체: CF-Connecting-IP, guards.py 참조)
- `require_user(request, use_case=Depends(get_auth_use_case)) -> SessionUserDTO` — `guard_auth == "off"`면 `SessionUserDTO(sub="dev", email="", name="dev")` 반환; 쿠키 `rd_session` 검증 실패 → `HTTPException(401, "로그인이 필요하다")`
- `ip_bucket(name: str, per_minute_attr: str)` → 의존성 팩토리; 버킷은 모듈 전역 dict `{name: TokenBucket}`(용량 = 분당 한도, 리필 = 한도/60). 초과 → `HTTPException(429, detail={"detail": "요청이 너무 잦다", "retry_after": ceil(wait)})` + `Retry-After` 헤더
- `GuardEvent(type="guard", layer: Literal["auth","user_daily","ip","daily_cap","length"], reason: str, ip_hash: str, user_sub: str | None)` — `session_id`는 판이 없을 수 있어 `uuid.UUID(int=0)` 고정 세션에 기록

- [ ] **Step 1: 실패하는 테스트**

```python
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from apps.engine.adapter.inbound.api.v1 import guards


def _app(monkeypatch, auth="on", per_minute=2):
    monkeypatch.setattr(guards, "_settings", lambda: type("S", (), {
        "guard_auth": auth, "ip_sessions_per_minute": per_minute, "ip_actions_per_minute": per_minute})())
    guards._BUCKETS.clear()
    app = FastAPI()

    @app.post("/g", dependencies=[Depends(guards.ip_bucket("sessions", "ip_sessions_per_minute"))])
    def g(user=Depends(guards.require_user)):
        return {"sub": user.sub}
    return app


def test_require_user_401_without_cookie(monkeypatch):
    app = _app(monkeypatch)
    app.dependency_overrides[guards.get_auth_use_case] = lambda: type("U", (), {"current_user": lambda self, t: None})()
    assert TestClient(app).post("/g").status_code == 401


def test_guard_auth_off_allows_anonymous(monkeypatch):
    app = _app(monkeypatch, auth="off")
    assert TestClient(app).post("/g").json() == {"sub": "dev"}


def test_ip_bucket_429_with_retry_after(monkeypatch):
    app = _app(monkeypatch, auth="off", per_minute=2)
    c = TestClient(app)
    assert c.post("/g").status_code == 200
    assert c.post("/g").status_code == 200
    r = c.post("/g")
    assert r.status_code == 429 and r.json()["detail"]["retry_after"] >= 1 and "Retry-After" in r.headers


# (09-17 대체: CF-Connecting-IP, guards.py 참조)
def test_client_ip_prefers_forwarded_for():
    from starlette.requests import Request
    scope = {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "203.0.113.9"
```

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현**

```python
# backend/apps/engine/adapter/inbound/api/v1/guards.py
"""과잉 사용 방지 의존성 — 로그인·IP 버킷·클라이언트 IP (설계: specs/2026-09-16-abuse-guard-design.md)."""

import hashlib
import math
import time

from fastapi import Depends, HTTPException, Request

from apps.engine.app.dtos.auth_dto import SessionUserDTO
from apps.engine.dependencies.engine_dependency import get_auth_use_case
from apps.engine.domain.entities.guard_rules import TokenBucket
from core.matrix.grid_keymaker_secret_manager import get_settings

SESSION_COOKIE = "rd_session"
_BUCKETS: dict[str, TokenBucket] = {}


def _settings():
    return get_settings()


# (09-17 대체: CF-Connecting-IP, guards.py 참조)
def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ip_hash(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:12]


def require_user(request: Request, use_case=Depends(get_auth_use_case)) -> SessionUserDTO:
    if _settings().guard_auth == "off":
        return SessionUserDTO(sub="dev", email="", name="dev")
    user = use_case.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요하다")
    return user


def ip_bucket(name: str, per_minute_attr: str):
    def dependency(request: Request) -> None:
        per_minute = getattr(_settings(), per_minute_attr)
        bucket = _BUCKETS.setdefault(name, TokenBucket(capacity=per_minute, refill_per_sec=per_minute / 60.0))
        ok, wait = bucket.take(client_ip(request), now=time.monotonic())
        if not ok:
            retry = max(1, math.ceil(wait))
            raise HTTPException(status_code=429, detail={"detail": "요청이 너무 잦다", "retry_after": retry},
                                headers={"Retry-After": str(retry)})
    return dependency
```

`GuardEvent`는 Task 4에서 판 생성 유스케이스가 기록한다(여기서는 DTO만 추가).

- [ ] **Step 4: 통과 확인** — 4 passed + 전체

---

### Task 4: 판 생성 — 사용자 하루 5판·전역 정원, 라우터 부착

**Files:**
- Modify: `backend/apps/engine/app/use_cases/session_interactor.py`, `backend/apps/engine/dependencies/engine_dependency.py:58-63`, `backend/apps/engine/adapter/inbound/api/v1/game_router.py:39-47,64-66,78-100,124-160`
- Test: `backend/tests/engine/test_guards.py`, `backend/tests/engine/test_e2e_flow.py`

**Interfaces:**
- `SessionInteractor.__init__(..., users, user_daily_attempts: int, daily_attempt_cap: int)`; `start(prior_attempt_id, user: SessionUserDTO) -> dict`
  - `user_id = users.get_by_sub(user.sub).id`(`guard_auth=off`의 "dev" sub는 `users.upsert_from_google(GoogleProfileDTO(sub="dev", email="dev@local", name="dev"))`로 만들어 둔다)
  - `count_today_all >= cap` → `DailyCapReached`; `count_today(user_id) >= limit` → `UserDailyLimit`. 둘 다 `GuardEvent` 기록 후 raise
- 라우터: `POST /sessions`에 `Depends(ip_bucket("sessions","ip_sessions_per_minute"))`, `user=Depends(require_user)`; 발화·비트·원숭이손·밤 초안·제출·질문·규칙 엔드포인트에 `Depends(require_user)` + 발화·질문에 `Depends(ip_bucket("actions","ip_actions_per_minute"))`. 조회 GET(notes·observations·npcs·journey·harness·inspector)은 그대로.
- 예외 매핑: `UserDailyLimit` → 403 `{"code":"daily_attempt_limit","detail":"오늘은 여기까지. 내일 다시 시작할 수 있다."}`, `DailyCapReached` → 503 `{"code":"daily_cap","detail":"오늘 정원이 마감됐다."}`
- `UtteranceReq.text: str = Field(max_length=200)`, `QuestionReq.text: str = Field(max_length=200)`

- [ ] **Step 1: 실패하는 테스트**

```python
def _login_override(app, sub="tester"):
    from apps.engine.adapter.inbound.api.v1 import guards
    from apps.engine.app.dtos.auth_dto import SessionUserDTO
    app.dependency_overrides[guards.require_user] = lambda: SessionUserDTO(sub=sub, email="t@x", name="t")


def test_sessions_require_login(db_session, monkeypatch):
    from main import app
    with TestClient(app) as c:
        assert c.post("/sessions", json={}).status_code == 401


def test_user_daily_limit_is_five(db_session, monkeypatch):
    from main import app
    _login_override(app)
    with TestClient(app) as c:
        for _ in range(5):
            assert c.post("/sessions", json={}).status_code == 200
        r = c.post("/sessions", json={})
        assert r.status_code == 403 and r.json()["code"] == "daily_attempt_limit"
    app.dependency_overrides.clear()


def test_daily_cap_blocks_new_sessions_only(db_session, monkeypatch):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings(); monkeypatch.setattr(s, "daily_attempt_cap", 1)
    _login_override(app)
    with TestClient(app) as c:
        first = c.post("/sessions", json={}).json()
        r = c.post("/sessions", json={})
        assert r.status_code == 503 and r.json()["code"] == "daily_cap"
        loop = c.post(f"/sessions/{first['attempt_id']}/loops")
        assert loop.status_code == 200  # 진행 중 판은 계속
    app.dependency_overrides.clear()


def test_text_length_limit(db_session):
    from main import app
    _login_override(app)
    with TestClient(app) as c:
        a = c.post("/sessions", json={}).json()
        loop = c.post(f"/sessions/{a['attempt_id']}/loops").json()
        r = c.post(f"/loops/{loop['loop_id']}/utterances", json={"target": "채연", "text": "가" * 201})
        assert r.status_code == 422
    app.dependency_overrides.clear()
```

`test_e2e_flow.py`의 `TestClient(app)` 사용 테스트에는 `_login_override(app)`을 붙인다(Settings의 `guard_auth`는 기본 "on"이므로).

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현** — 위 인터페이스대로. `get_session_interactor`에 `users=UserRepository(session)`, 한도 두 값을 settings에서. 라우터의 예외 → 응답 매핑은 기존 `GameStateError` 처리 패턴(`game_router.py` 상단 import·`HTTPException` 변환) 옆에 추가. `UserRepository.get_by_sub`가 없으면 추가(`upsert_from_google` 옆).
- [ ] **Step 4: 통과 확인** — 전체 스위트 green(기존 e2e 포함). 셀프플레이 러너는 Task 6에서.

---

### Task 5: 프런트 — 401·403·503 화면과 헤드리스

**Files:**
- Create: `frontend/components/screens/GuardScreen.tsx`
- Modify: `frontend/contracts/api.ts` (`ApiError.code?: string` — 응답 JSON의 `code` 보존), `frontend/app/play/page.tsx:105-150` (sessionAction 실패 분기)
- Test: `frontend/tests/guard.cjs`

**Interfaces:**
- `GuardScreen({ kind: "login" | "daily_limit" | "daily_cap" | "rate", retryAfter?: number })` — 문구: login "로그인이 필요하다. 랜딩에서 구글로 시작해라." + 링크 `/`; daily_limit "오늘은 여기까지. 내일 다시 시작할 수 있다."; daily_cap "오늘 정원이 마감됐다. 내일 다시 열린다."; rate "요청이 너무 잦다. {n}초 뒤 다시."
- `page.tsx`: `sessionAction.failure`가 `ApiError`이고 status 401/403(code daily_attempt_limit)/503(code daily_cap)/429이면 기존 실패 배너 대신 `GuardScreen` 렌더.

- [ ] **Step 1: 헤드리스 테스트(실패부터)** — `guard.cjs`: 모의 `/sessions`가 401 → "로그인이 필요하다" 표시 + 랜딩 링크; 403 `{code:"daily_attempt_limit"}` → "오늘은 여기까지"; 503 `{code:"daily_cap"}` → "정원이 마감"; 429 `{detail:{retry_after: 7}}` → "7초". 각 케이스 390px에서 스크린샷.
- [ ] **Step 2: 구현** — `request()`에서 JSON 본문의 `code`를 `ApiError.code`에 실음. GuardScreen은 기존 화면 스타일(`bg-void text-paper`, 버튼 클래스) 재사용.
- [ ] **Step 3: 검증** — `npx tsc --noEmit`; `guard.cjs`, `gameplay-clarity.cjs` 순차 통과.

---

### Task 6: 러너·문서·재검증

**Files:**
- Modify: `backend/scripts/run_selfplay.py`(+ `runner_common.py`): `--session-cookie` 옵션 → `httpx` 클라이언트 `cookies={"rd_session": ...}`; 없으면 `.env`의 `GUARD_AUTH=off`를 안내하는 에러 메시지
- Modify: `docs/spec/api_contract.md`(401/403/429/503 계약, 200자, `user_id`), `docs/HANDOFF-26-09-16.md`(허들 완료, 운영 메모: 로컬 러너는 `GUARD_AUTH=off`, 프로덕션은 on + Anthropic 콘솔 지출 한도), `start_demo.sh`는 무변경(`.env`가 정본)

- [ ] **Step 1:** 러너 옵션 구현, dry 실행으로 인자 파싱 확인
- [ ] **Step 2:** 문서 갱신
- [ ] **Step 3:** 전체 재검증 — 백엔드 전체, `tsc`, 헤드리스 8종(기존 7 + guard). 세션 주인에게 보고. 커밋·머지·`alembic upgrade head`·재기동은 세션 주인이 한다.
