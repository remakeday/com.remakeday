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
        "guard_auth": auth, "ip_sessions_per_minute": per_minute, "ip_actions_per_minute": per_minute,
        "trust_proxy": False})())
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


def test_client_ip_prefers_forwarded_for(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", True)
    scope = {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "203.0.113.9"


def test_client_ip_ignores_forwarded_for_when_not_trusted(monkeypatch):
    from starlette.requests import Request
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "trust_proxy", False)
    scope = {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.1")], "client": ("127.0.0.1", 1)}
    assert guards.client_ip(Request(scope)) == "127.0.0.1"


def test_sessions_require_login(db_session, monkeypatch):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    guards._BUCKETS.clear()
    with TestClient(app) as c:
        assert c.post("/sessions", json={}).status_code == 401


def test_user_daily_limit_is_five(db_session, monkeypatch, logged_in):
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    # IP 분당 버킷(기본 5)이 하루 5판 한도와 같은 수라 6번째 호출에서 충돌한다 —
    # 이 테스트는 사용자 하루 한도만 겨냥하므로 IP 버킷은 넉넉히 풀어둔다.
    monkeypatch.setattr(cfg.get_settings(), "ip_sessions_per_minute", 1000)
    with TestClient(app) as c:
        for _ in range(5):
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


def test_free_text_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        r = c.post(f"/loops/{uuid.uuid4()}/night/draft", json={"free_text": "가" * 2001})
        assert r.status_code == 422


def test_claims_count_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        r = c.patch(f"/nights/{uuid.uuid4()}/claims", json={"claims": ["주장"] * 9})
        assert r.status_code == 422


def test_claim_length_limit(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        r = c.patch(f"/nights/{uuid.uuid4()}/claims", json={"claims": ["가" * 501]})
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
