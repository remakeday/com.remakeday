import json
import uuid
from datetime import datetime, timezone, timedelta

import pytest

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


from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from apps.engine.adapter.inbound.api.v1 import guards


def _app(monkeypatch, auth="on", per_minute=2):
    monkeypatch.setattr(guards, "_settings", lambda: type("S", (), {
        "guard_auth": auth, "auth_required": auth != "off", "ip_sessions_per_minute": per_minute,
        "ip_actions_per_minute": per_minute, "trust_proxy": False})())
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


def test_guard_auth_off_rejects_request_via_cloudflare(monkeypatch):
    """off로 떠 있어도 Cloudflare(터널)를 거친 요청은 `dev`로 통과시키지 않는다 — .env 프론트 주소가 틀려도 공개 우회 차단."""
    app = _app(monkeypatch, auth="off")
    r = TestClient(app).post("/g", headers={"CF-Connecting-IP": "203.0.113.9"})
    assert r.status_code == 403
    assert "code" not in r.json()  # daily_attempt_limit 같은 허들 화면으로 오해되지 않는다


def test_guard_auth_on_ignores_cloudflare_header(monkeypatch):
    app = _app(monkeypatch, auth="on")
    user = type("User", (), {"sub": "u-1"})()
    app.dependency_overrides[guards.get_auth_use_case] = lambda: type("U", (), {"current_user": lambda self, t: user})()
    r = TestClient(app).post("/g", headers={"CF-Connecting-IP": "203.0.113.9"})
    assert r.status_code == 200 and r.json() == {"sub": "u-1"}


def test_guard_auth_off_cloudflare_rejection_records_guard_event(db_session, monkeypatch):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
    from apps.engine.domain.value_objects.event_type import EventType
    from sqlalchemy import select
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "off")
    guards._BUCKETS.clear()
    with TestClient(app) as c:
        assert c.post("/sessions", json={}, headers={"CF-Connecting-IP": "203.0.113.9"}).status_code == 403
    rows = db_session.scalars(select(EventLogOrm).where(EventLogOrm.type == str(EventType.GUARD))).all()
    assert any(r.payload.get("layer") == "auth" and r.payload.get("reason") == "guard_auth_off_via_proxy" for r in rows)


def test_ip_bucket_429_with_retry_after(monkeypatch):
    app = _app(monkeypatch, auth="off", per_minute=2)
    c = TestClient(app)
    assert c.post("/g").status_code == 200
    assert c.post("/g").status_code == 200
    r = c.post("/g")
    assert r.status_code == 429 and r.json()["detail"]["retry_after"] >= 1 and "Retry-After" in r.headers


def test_client_ip_uses_cf_connecting_ip_when_trusted(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", True)
    scope = {"type": "http", "headers": [(b"cf-connecting-ip", b"203.0.113.9")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "203.0.113.9"


def test_client_ip_ignores_spoofed_forwarded_for_when_trusted(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", True)
    scope = {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "127.0.0.1"


def test_client_ip_prefers_cf_connecting_ip_over_forwarded_for(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", True)
    scope = {"type": "http", "headers": [
        (b"x-forwarded-for", b"198.51.100.1, 10.0.0.1"),
        (b"cf-connecting-ip", b"203.0.113.9"),
    ], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "203.0.113.9"


def test_client_ip_ignores_forwarded_for_when_not_trusted(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", False)
    scope = {"type": "http", "headers": [
        (b"x-forwarded-for", b"203.0.113.9, 10.0.0.1"),
        (b"cf-connecting-ip", b"203.0.113.9"),
    ], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "127.0.0.1"


def test_client_ip_falls_back_when_cf_connecting_ip_is_invalid(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", True)
    scope = {"type": "http", "headers": [(b"cf-connecting-ip", b"   ")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "127.0.0.1"
    scope2 = {"type": "http", "headers": [(b"cf-connecting-ip", b"not-an-ip")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope2)) == "127.0.0.1"


def test_sessions_require_login(db_session, monkeypatch):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    guards._BUCKETS.clear()
    with TestClient(app) as c:
        assert c.post("/sessions", json={}).status_code == 401


def test_user_daily_limit_is_three(db_session, monkeypatch, logged_in):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    # IP 분당 버킷(기본 5)이 하루 판 한도보다 커서, 이 테스트는 사용자 하루 한도만 겨냥한다.
    monkeypatch.setattr(cfg.get_settings(), "ip_sessions_per_minute", 1000)
    with TestClient(app) as c:
        for _ in range(3):
            assert c.post("/sessions", json={}).status_code == 200
        r = c.post("/sessions", json={})
        assert r.status_code == 403 and r.json()["code"] == "daily_attempt_limit"


def test_daily_cap_blocks_new_sessions_only(db_session, monkeypatch, logged_in):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings(); monkeypatch.setattr(s, "daily_attempt_cap", 1)
    with TestClient(app) as c:
        first = c.post("/sessions", json={}).json()
        r = c.post("/sessions", json={})
        assert r.status_code == 503 and r.json()["code"] == "daily_cap"
        loop = c.post(f"/sessions/{first['attempt_id']}/loops")
        assert loop.status_code == 200  # 진행 중 판은 계속


def test_text_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        a = c.post("/sessions", json={}).json()
        loop = c.post(f"/sessions/{a['attempt_id']}/loops").json()
        r = c.post(f"/loops/{loop['loop_id']}/utterances", json={"target": "채연", "text": "가" * 201})
        assert r.status_code == 422


def _own_loop_and_night(c, db_session):
    """본문 상한 검사용 — 판 주인 확인(F26)을 통과하는 내 회차·밤 ID."""
    from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm
    from apps.engine.adapter.outbound.repositories.game_repository import NightRepository
    a = c.post("/sessions", json={}).json()
    loop_id = c.post(f"/sessions/{a['attempt_id']}/loops").json()["loop_id"]
    night = NightRepository(db_session).create(NightOrm(loop_id=uuid.UUID(loop_id)))
    return loop_id, night.id


def test_free_text_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        loop_id, _ = _own_loop_and_night(c, db_session)
        r = c.post(f"/loops/{loop_id}/night/draft", json={"free_text": "가" * 2001})
        assert r.status_code == 422


def test_claims_count_limit(db_session, logged_in):
    from apps.engine.app.use_cases.night_interactor import MAX_CLAIMS
    from main import app
    with TestClient(app) as c:
        _, night_id = _own_loop_and_night(c, db_session)
        r = c.patch(f"/nights/{night_id}/claims", json={"claims": ["주장"] * (MAX_CLAIMS + 1)})
        assert r.status_code == 422


def test_claim_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        _, night_id = _own_loop_and_night(c, db_session)
        r = c.patch(f"/nights/{night_id}/claims", json={"claims": ["가" * 501]})
        assert r.status_code == 422


def test_rule_custom_text_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        _, night_id = _own_loop_and_night(c, db_session)
        r = c.post(f"/nights/{night_id}/rule", json={"choice": "custom", "custom_text": "가" * 201})
        assert r.status_code == 422


def test_rule_preview_custom_text_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        _, night_id = _own_loop_and_night(c, db_session)
        r = c.post(f"/nights/{night_id}/rule/preview", json={"custom_text": "가" * 201})
        assert r.status_code == 422


def test_require_user_401_records_guard_event(db_session, monkeypatch):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
    from apps.engine.domain.value_objects.event_type import EventType
    from sqlalchemy import select
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    guards._BUCKETS.clear()
    with TestClient(app) as c:
        assert c.post("/sessions", json={}).status_code == 401
    # session_id는 임의의 uuid4라 조회 키로 못 쓴다 — layer로 직접 확인한다
    rows = db_session.scalars(select(EventLogOrm).where(EventLogOrm.type == str(EventType.GUARD))).all()
    assert any(r.payload.get("layer") == "auth" for r in rows)


def test_lifespan_rejects_default_session_secret_when_guard_auth_on(monkeypatch):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    monkeypatch.setattr(s, "guard_auth", "on")
    monkeypatch.setattr(s, "session_secret", "dev-session-secret-change-me")
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        with TestClient(app):
            pass


def test_lifespan_rejects_default_session_secret_for_any_auth_on_value(monkeypatch):
    """`off`가 아니면 인증이 켜진다(guards와 같은 판정) — `On` 같은 값도 기본 SESSION_SECRET 검사를 건너뛰지 않는다."""
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    monkeypatch.setattr(s, "guard_auth", "On")
    monkeypatch.setattr(s, "session_secret", "dev-session-secret-change-me")
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        with TestClient(app):
            pass


def test_lifespan_rejects_guard_auth_off_on_public_deploy(monkeypatch):
    """공개 배포(https 프론트)에서 GUARD_AUTH=off면 모든 요청이 `dev` 한 사용자가 되므로 기동을 거부한다."""
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    monkeypatch.setattr(s, "frontend_base_url", "https://remakeday.example")
    monkeypatch.setattr(s, "guard_auth", "off")
    with pytest.raises(RuntimeError, match="GUARD_AUTH"):
        with TestClient(app):
            pass


@pytest.mark.parametrize("frontend,auth", [
    ("https://remakeday.example", "on"),
    ("http://localhost:3500", "off"),  # 로컬·러너
    ("http://localhost:3500", "on"),
])
def test_lifespan_starts_when_auth_mode_fits_deploy(db_session, monkeypatch, frontend, auth):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    monkeypatch.setattr(s, "frontend_base_url", frontend)
    monkeypatch.setattr(s, "guard_auth", auth)
    monkeypatch.setattr(s, "session_secret", "test-secret-f26b")
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200


@pytest.mark.parametrize("frontend,public", [
    ("https://remakeday.example", True),
    ("http://localhost:3500", False),
    ("http://127.0.0.1:3500", False),
])
def test_public_deploy_is_decided_by_frontend_scheme(frontend, public):
    from core.matrix.grid_keymaker_secret_manager import Settings
    assert Settings(database_url="postgresql://x", frontend_base_url=frontend).public_deploy is public


def test_max_body_size_middleware_rejects_oversized_content_length():
    import asyncio
    from main import MaxBodySizeMiddleware

    inner_called = []

    async def inner_app(scope, receive, send):
        inner_called.append(True)

    sent = []

    async def send(message):
        sent.append(message)

    async def receive():
        return {"type": "http.disconnect"}

    scope = {"type": "http", "headers": [(b"content-length", b"300000")]}
    asyncio.run(MaxBodySizeMiddleware(inner_app)(scope, receive, send))
    assert inner_called == []
    start = next(m for m in sent if m["type"] == "http.response.start")
    assert start["status"] == 413
    body = b"".join(m["body"] for m in sent if m["type"] == "http.response.body")
    assert json.loads(body) == {"detail": "요청이 너무 크다"}


def test_max_body_size_middleware_passes_through_without_content_length():
    import asyncio
    from main import MaxBodySizeMiddleware

    inner_called = []

    async def inner_app(scope, receive, send):
        inner_called.append(True)

    scope = {"type": "http", "headers": []}
    asyncio.run(MaxBodySizeMiddleware(inner_app)(scope, lambda: None, lambda m: None))
    assert inner_called == [True]
