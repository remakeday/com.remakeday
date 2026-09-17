"""F26 — 판 API 소유자 확인. 남의 판·없는 판은 존재 여부를 흘리지 않게 404로 같게 거부한다."""

import uuid

import pytest

from apps.engine.adapter.outbound.orms.game_state_orm import LoopOrm, NightOrm
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
)
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO, SessionUserDTO
from apps.engine.app.use_cases.attempt_access_interactor import (
    AttemptAccessInteractor,
    AttemptNotFound,
)


def _user(sub: str) -> SessionUserDTO:
    return SessionUserDTO(sub=sub, email=f"{sub}@x", name=sub)


def _seed_game(db_session, sub: str) -> dict:
    """sub 사용자의 판 하나 + 회차 + 밤 — ID 묶음을 돌려준다."""
    owner = UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email="", name=sub))
    attempt = AttemptRepository(db_session).create(None, user_id=owner.id)
    loop = LoopRepository(db_session).create(LoopOrm(attempt_id=attempt.id, loop_n=1, budget_left=8), [])
    night = NightRepository(db_session).create(NightOrm(loop_id=loop.id))
    return {"attempt_id": str(attempt.id), "loop_id": str(loop.id), "night_id": str(night.id)}


def _access(db_session) -> AttemptAccessInteractor:
    return AttemptAccessInteractor(
        attempts=AttemptRepository(db_session),
        loops=LoopRepository(db_session),
        nights=NightRepository(db_session),
        users=UserRepository(db_session),
    )


# ── Task 1: 소유 판정 유스케이스 ──────────────────────────────


@pytest.mark.parametrize("kind", ["attempt_id", "loop_id", "night_id"])
def test_owner_passes_for_every_id_kind(db_session, kind):
    ids = _seed_game(db_session, "alice")
    _access(db_session).ensure_owner({kind: ids[kind]}, _user("alice"))


@pytest.mark.parametrize("kind", ["attempt_id", "loop_id", "night_id"])
def test_other_user_is_denied_for_every_id_kind(db_session, kind):
    ids = _seed_game(db_session, "alice")
    _seed_game(db_session, "bob")
    with pytest.raises(AttemptNotFound):
        _access(db_session).ensure_owner({kind: ids[kind]}, _user("bob"))


@pytest.mark.parametrize("kind", ["attempt_id", "loop_id", "night_id"])
def test_missing_id_is_denied_like_foreign(db_session, kind):
    _seed_game(db_session, "alice")
    with pytest.raises(AttemptNotFound):
        _access(db_session).ensure_owner({kind: str(uuid.uuid4())}, _user("alice"))


def test_invalid_uuid_is_denied(db_session):
    _seed_game(db_session, "alice")
    with pytest.raises(AttemptNotFound):
        _access(db_session).ensure_owner({"loop_id": "not-a-uuid"}, _user("alice"))


def test_legacy_attempt_without_user_is_denied(db_session):
    UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub="alice", email="", name="a"))
    legacy = AttemptRepository(db_session).create(None)  # user_id 없는 구판
    with pytest.raises(AttemptNotFound):
        _access(db_session).ensure_owner({"attempt_id": str(legacy.id)}, _user("alice"))


def test_session_without_users_row_is_denied(db_session):
    ids = _seed_game(db_session, "alice")
    with pytest.raises(AttemptNotFound):
        _access(db_session).ensure_owner({"attempt_id": ids["attempt_id"]}, _user("stranger"))


def test_route_without_game_id_is_denied_fail_closed(db_session):
    _seed_game(db_session, "alice")
    with pytest.raises(AttemptNotFound):
        _access(db_session).ensure_owner({}, _user("alice"))


def test_route_without_game_id_is_denied_before_user_lookup():
    """판 ID가 없는 경로는 users를 조회하기 전에 거부한다."""

    class _NoLookupUsers:
        def get_by_sub(self, sub):
            raise AssertionError("판 ID 없는 경로에서 users를 조회했다")

    access = AttemptAccessInteractor(attempts=None, loops=None, nights=None, users=_NoLookupUsers())
    with pytest.raises(AttemptNotFound):
        access.ensure_owner({"other_id": "x"}, _user("alice"))


def test_get_owned_matches_user(db_session):
    ids = _seed_game(db_session, "alice")
    alice = UserRepository(db_session).get_by_sub("alice")
    repo = AttemptRepository(db_session)
    attempt_id = uuid.UUID(ids["attempt_id"])
    assert repo.get_owned(attempt_id, alice.id).id == attempt_id
    assert repo.get_owned(attempt_id, uuid.uuid4()) is None


# ── Task 2: 라우터 강제 (HTTP) ────────────────────────────────

from fastapi.testclient import TestClient  # noqa: E402

# 판에 속한 라우트 전수 — (메서드, 경로 틀, 유효한 본문)
GAME_ROUTES = [
    ("POST", "/sessions/{attempt_id}/loops", None),
    ("POST", "/loops/{loop_id}/utterances", {"target": "x", "text": "안녕"}),
    ("POST", "/loops/{loop_id}/beats/next", None),
    ("POST", "/loops/{loop_id}/paw/respond", {"offer_id": "o", "accept": True}),
    ("GET", "/loops/{loop_id}/notes", None),
    ("GET", "/loops/{loop_id}/observations", None),
    ("GET", "/loops/{loop_id}/night/previous", None),
    ("GET", "/loops/{loop_id}/npcs", None),
    ("POST", "/loops/{loop_id}/night/draft", {"tapped_note_ids": [], "free_text": "x"}),
    ("PATCH", "/nights/{night_id}/claims", {"claims": ["x"]}),
    ("POST", "/nights/{night_id}/submit", None),
    ("POST", "/nights/{night_id}/questions", {"text": "무슨 일?"}),
    ("GET", "/nights/{night_id}/options", None),
    ("POST", "/nights/{night_id}/rule", {"choice": "1"}),
    ("POST", "/nights/{night_id}/rule/preview", {"custom_text": "x"}),
    ("GET", "/attempts/{attempt_id}/journey", None),
    ("GET", "/attempts/{attempt_id}/harness", None),
]
_ROUTE_IDS = [f"{m} {p}" for m, p, _ in GAME_ROUTES]


def _call(client, method, template, body, ids):
    return client.request(method, template.format(**ids), json=body)


@pytest.fixture
def as_user(monkeypatch):
    """require_user를 원하는 sub로 바꿔 끼운다 — 테스트 끝에 정리."""
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg

    monkeypatch.setattr(cfg.get_settings(), "ip_actions_per_minute", 1000)
    guards._BUCKETS.clear()

    def switch(sub: str) -> None:
        app.dependency_overrides[guards.require_user] = lambda: _user(sub)

    try:
        yield switch
    finally:
        app.dependency_overrides.pop(guards.require_user, None)
        guards._BUCKETS.clear()


def _game_snapshot(db_session, ids) -> dict:
    """주인 판의 상태 — 비주인 요청 전후 비교용(이벤트 수·회차·밤·판 상태)."""
    from sqlalchemy import func, select

    from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
    from apps.engine.adapter.outbound.orms.game_state_orm import AttemptOrm

    db_session.expire_all()
    attempt_id = uuid.UUID(ids["attempt_id"])
    loops = db_session.scalars(select(LoopOrm).where(LoopOrm.attempt_id == attempt_id).order_by(LoopOrm.loop_n)).all()
    night = db_session.get(NightOrm, uuid.UUID(ids["night_id"]))
    return {
        "events": db_session.scalar(select(func.count()).select_from(EventLogOrm).where(EventLogOrm.session_id == attempt_id)),
        "attempt_status": db_session.get(AttemptOrm, attempt_id).status,
        "loops": [(lp.loop_n, lp.state, lp.beat, lp.budget_left) for lp in loops],
        "night": (night.submitted, night.claims, night.free_text, night.tapped_note_ids, night.edit_count),
    }


@pytest.mark.parametrize("method,template,body", GAME_ROUTES, ids=_ROUTE_IDS)
def test_other_users_game_is_404_on_every_route(db_session, as_user, method, template, body):
    from main import app
    ids = _seed_game(db_session, "alice")
    _seed_game(db_session, "bob")
    as_user("bob")
    with TestClient(app) as client:
        before = _game_snapshot(db_session, ids)
        res = _call(client, method, template, body, ids)
        after = _game_snapshot(db_session, ids)
    assert res.status_code == 404
    assert res.json() == {"detail": "판을 찾을 수 없다"}
    assert after == before  # 거부된 요청은 주인 판에 아무것도 남기지 않는다


@pytest.mark.parametrize("method,template,body", GAME_ROUTES, ids=_ROUTE_IDS)
def test_anonymous_is_401_on_every_route(db_session, monkeypatch, method, template, body):
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    guards._BUCKETS.clear()
    ids = _seed_game(db_session, "alice")
    with TestClient(app) as client:
        res = _call(client, method, template, body, ids)
    assert res.status_code == 401


def test_owner_reads_own_game(db_session, as_user):
    from main import app
    ids = _seed_game(db_session, "alice")
    as_user("alice")
    with TestClient(app) as client:
        assert client.get(f"/loops/{ids['loop_id']}/notes").status_code == 200
        assert client.get(f"/loops/{ids['loop_id']}/observations").status_code == 200
        assert client.get(f"/loops/{ids['loop_id']}/night/previous").status_code == 200


def test_invalid_id_is_404_not_422(db_session, as_user):
    from main import app
    _seed_game(db_session, "alice")
    as_user("alice")
    with TestClient(app) as client:
        assert client.get("/loops/not-a-uuid/notes").status_code == 404


def test_inspector_keeps_token_auth_without_login(db_session, monkeypatch):
    """인스펙터는 로그인 없이 `X-Inspector-Token` 헤더로만 연다 — 쿼리스트링 토큰은 받지 않는다(접근 로그 노출)."""
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    token = cfg.get_settings().inspector_token  # conftest의 테스트 전용 값
    ids = _seed_game(db_session, "alice")
    with TestClient(app) as client:
        url = f"/attempts/{ids['attempt_id']}/inspector"
        assert client.get(url, headers={"X-Inspector-Token": "wrong"}).status_code == 403
        assert client.get(url).status_code == 403
        assert client.get(url, params={"token": token}).status_code == 403
        assert client.get(url, headers={"X-Inspector-Token": token}).status_code == 200


def test_inspector_is_404_when_token_unset(db_session, monkeypatch):
    """INSPECTOR_TOKEN 미설정이면 인스펙터 라우트는 없는 것처럼 404 — 빈 토큰으로 열리지 않는다."""
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "inspector_token", "")
    ids = _seed_game(db_session, "alice")
    with TestClient(app) as client:
        url = f"/attempts/{ids['attempt_id']}/inspector"
        assert client.get(url).status_code == 404
        assert client.get(url, headers={"X-Inspector-Token": ""}).status_code == 404
        assert client.get(url, headers={"X-Inspector-Token": "anything"}).status_code == 404


def test_inspector_token_has_no_code_default():
    from core.matrix.grid_keymaker_secret_manager import Settings
    assert Settings.model_fields["inspector_token"].default == ""


def test_inspector_compares_token_in_constant_time(monkeypatch):
    from apps.engine.app.use_cases import inspector_interactor as mod
    calls = []
    real = mod.hmac.compare_digest
    monkeypatch.setattr(mod.hmac, "compare_digest", lambda a, b: calls.append((a, b)) or real(a, b))
    uc = mod.InspectorInteractor(attempts=None, rules=None, event_log=None, inspector_token="secret")
    with pytest.raises(mod.AccessDenied):
        uc.inspector_view(uuid.uuid4(), "wrong")
    assert calls
    with pytest.raises(mod.AccessDenied):
        uc.inspector_view(uuid.uuid4(), "토큰")  # 비ASCII도 500(TypeError)이 아니라 403


def test_public_deploy_has_no_api_docs_routes():
    """운영 설정(https 프론트)으로 띄운 앱에는 /docs·/redoc·/openapi.json이 없다 — 새 프로세스에서 import해 확인."""
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    code = (
        "import json, main\n"
        "from fastapi.routing import iter_route_contexts\n"
        "from fastapi.testclient import TestClient\n"
        "c = TestClient(main.app)\n"
        "paths = sorted({ctx.path for ctx in iter_route_contexts(main.app.routes)})\n"
        "status = {p: c.get(p).status_code for p in ['/docs', '/docs/oauth2-redirect', '/redoc', '/openapi.json']}\n"
        "print(json.dumps({'paths': paths, 'status': status}))\n"
    )
    env = {**os.environ, "FRONTEND_BASE_URL": "https://remakeday.example"}
    out = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[2],
                         env=env, capture_output=True, text=True, check=True).stdout
    result = json.loads(out.strip().splitlines()[-1])
    assert not {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"} & set(result["paths"])
    assert set(result["status"].values()) == {404}
    assert "/sessions" in result["paths"]  # 게임 라우트는 그대로


# 로그인·판 주인 확인 없이 열려 있는 라우트 — 여기 없는 라우트는 전부 `require_attempt_owner`를 가져야 한다.
PUBLIC_ROUTES = {
    ("GET", "/health"),
    ("POST", "/sessions"),  # 로그인만(판 생성 전) — 남의 prior_attempt_id는 유스케이스가 무시
    ("GET", "/attempts/{attempt_id}/inspector"),  # 인스펙터 토큰 인증
    ("GET", "/api/v1/auth/google/start"),
    ("GET", "/api/v1/auth/google/callback"),
    ("POST", "/api/v1/auth/dev/login"),
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/logout"),
    # FastAPI 문서 라우트 — 개발(로컬) 설정에만 있다. 운영 설정에서 없는지는 test_public_deploy_has_no_api_docs_routes.
    ("GET", "/openapi.json"),
    ("GET", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
}


def _app_route_table(app) -> dict[tuple[str, str], bool]:
    """앱의 실제 라우트 전부(include_in_schema=False·문서 라우트 포함) → 판 주인 의존성 보유 여부."""
    from fastapi.routing import iter_route_contexts

    from apps.engine.adapter.inbound.api.v1 import guards

    def calls(dependant) -> set:
        found = set()
        for sub in dependant.dependencies:
            found |= {sub.call} | calls(sub)
        return found

    table = {}
    for ctx in iter_route_contexts(app.routes):
        dependant = getattr(ctx, "dependant", None)
        owner = dependant is not None and guards.require_attempt_owner in calls(dependant)
        for method in (ctx.methods or set()) - {"HEAD"}:
            table[(method, ctx.path)] = owner
    return table


def test_route_table_every_non_public_route_requires_owner():
    """허용 목록 밖 라우트는 전부 주인 확인 — owned 밖에 새 라우트를 달거나 옮기면 여기서 걸린다."""
    from main import app

    table = _app_route_table(app)
    assert PUBLIC_ROUTES <= table.keys(), f"허용 목록에 없는 라우트: {PUBLIC_ROUTES - table.keys()}"
    unguarded = {key for key, owner in table.items() if key not in PUBLIC_ROUTES and not owner}
    assert not unguarded, f"판 주인 확인 없는 비공개 라우트: {unguarded}"
    # 보호 라우트 전부가 위 HTTP 전수 테스트(GAME_ROUTES)에 들어 있다
    assert {key for key in table if key not in PUBLIC_ROUTES} == {(m, p) for m, p, _ in GAME_ROUTES}


# ── Task 3: 이어하기(prior)·예외 경로 ─────────────────────────


def test_foreign_prior_attempt_is_ignored_like_missing(db_session, as_user, monkeypatch):
    """남의 판을 prior로 넘기면 없는 판처럼 새 1회차 — 그 판의 점수가 새지 않는다."""
    from main import app
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "ip_sessions_per_minute", 1000)
    ids = _seed_game(db_session, "alice")
    alice_attempt = AttemptRepository(db_session).get(uuid.UUID(ids["attempt_id"]))
    alice_attempt.prior_cell_results = {"cause": 90, "motive": 80, "side_effect": 70, "identity": 60}
    db_session.commit()
    with TestClient(app) as client:
        as_user("bob")
        res = client.post("/sessions", json={"prior_attempt_id": ids["attempt_id"]})
        assert res.status_code == 200
        assert res.json()["attempt_n"] == 1 and res.json()["prior_cell_results"] is None
        as_user("alice")
        mine = client.post("/sessions", json={"prior_attempt_id": ids["attempt_id"]}).json()
        assert mine["attempt_n"] == 2 and mine["prior_cell_results"]["cause"] == 90


def test_malformed_prior_attempt_id_is_422(db_session, as_user, monkeypatch):
    """UUID가 아닌 prior는 요청 형식 오류 — 500이 아니라 422, 판도 만들지 않는다."""
    from sqlalchemy import func, select

    from main import app
    from apps.engine.adapter.outbound.orms.game_state_orm import AttemptOrm
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "ip_sessions_per_minute", 1000)
    with TestClient(app) as client:
        as_user("alice")
        res = client.post("/sessions", json={"prior_attempt_id": "not-a-uuid"})
    assert res.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(AttemptOrm)) == 0


@pytest.fixture
def real_auth(db_session, monkeypatch):
    """실제 세션 쿠키 경로 — GUARD_AUTH=on, 개발 계정 로그인 on."""
    from apps.engine.adapter.inbound.api.v1 import auth_router, guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    for key, value in {"guard_auth": "on", "dev_login": "on", "dev_account_id": "test-dev",
                       "dev_account_password": "test-pass-123", "session_secret": "test-secret-f26",
                       "ip_sessions_per_minute": 1000, "frontend_base_url": "http://localhost:3500"}.items():
        monkeypatch.setattr(s, key, value)
    guards._BUCKETS.clear()
    auth_router._DEV_LOGIN_BUCKET.clear()
    yield s
    guards._BUCKETS.clear()
    auth_router._DEV_LOGIN_BUCKET.clear()


def _dev_client(app):
    client = TestClient(app)
    res = client.post("/api/v1/auth/dev/login", json={"id": "test-dev", "password": "test-pass-123"})
    assert res.status_code == 200
    return client


def test_dev_account_game_continues_from_another_session(real_auth):
    """같은 개발 계정이면 브라우저·세션이 달라도 그 판을 이어 쓴다(주인 판정은 sub `dev:{id}` 기준)."""
    from main import app
    from apps.engine.adapter.outbound.security.session_token_signer import SessionTokenSigner
    with TestClient(app):  # lifespan(시드) 1회
        first = _dev_client(app)
        attempt_id = first.post("/sessions", json={}).json()["attempt_id"]
        loop = first.post(f"/sessions/{attempt_id}/loops").json()

        second = _dev_client(app)  # 다른 세션(쿠키 따로)
        assert second.get(f"/loops/{loop['loop_id']}/notes").status_code == 200
        assert second.get(f"/loops/{loop['loop_id']}/npcs").status_code == 200

        google = TestClient(app)
        token = SessionTokenSigner(real_auth.session_secret).issue(
            SessionUserDTO(sub="google-carol", email="c@x", name="c"), 3600)
        google.cookies.set("rd_session", token)
        assert google.post("/sessions", json={}).status_code == 200  # 자기 판은 만들 수 있다
        assert google.get(f"/loops/{loop['loop_id']}/notes").status_code == 404
        assert google.post(f"/sessions/{attempt_id}/loops").status_code == 404


def test_guard_auth_off_uses_dev_identity_for_ownership(db_session, monkeypatch):
    """GUARD_AUTH=off(로컬·러너)는 로그인 없이 자기(`dev`) 판을 계속 쓰되, 로그인 사용자의 판은 열리지 않는다."""
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "off")
    monkeypatch.setattr(cfg.get_settings(), "ip_sessions_per_minute", 1000)
    guards._BUCKETS.clear()
    alice = _seed_game(db_session, "alice")
    with TestClient(app) as client:
        attempt_id = client.post("/sessions", json={}).json()["attempt_id"]
        loop = client.post(f"/sessions/{attempt_id}/loops")
        assert loop.status_code == 200
        assert client.get(f"/loops/{loop.json()['loop_id']}/notes").status_code == 200
        assert client.get(f"/loops/{alice['loop_id']}/notes").status_code == 404
    guards._BUCKETS.clear()
