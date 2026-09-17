"""개발 계정 로그인 — DEV_LOGIN=on 일 때만 열리는 POST /api/v1/auth/dev/login."""

import pytest
from fastapi.testclient import TestClient

from apps.engine.adapter.inbound.api.v1 import auth_router
from apps.engine.app.dtos.auth_dto import DevAccountDTO, GoogleProfileDTO, SessionUserDTO
from apps.engine.app.use_cases.auth_interactor import AuthInteractor
from apps.engine.adapter.outbound.security.session_token_signer import SessionTokenSigner

# 가짜 테스트 픽스처 값 — 실제 개발 계정 값은 backend/.env(DEV_ACCOUNT_ID/DEV_ACCOUNT_PASSWORD)에만 있다.
DEV_ACCOUNT_ID = "test-dev"
DEV_ACCOUNT_PASSWORD = "test-pass-123"
WRONG_ACCOUNT_ID = "test-dev-2"
WRONG_PASSWORD = DEV_ACCOUNT_PASSWORD + "0"
DEV_SUB = f"dev:{DEV_ACCOUNT_ID}"


class _Users:
    def __init__(self):
        self.saved = []

    def upsert_from_google(self, profile: GoogleProfileDTO):
        self.saved.append(profile)
        return type("U", (), {"id": 1, "google_sub": profile.sub, "email": profile.email,
                              "name": profile.name, "picture": profile.picture})()

    def get_by_sub(self, sub):
        return None


def _interactor(dev=DevAccountDTO(account_id=DEV_ACCOUNT_ID, password=DEV_ACCOUNT_PASSWORD)):
    return AuthInteractor(oauth=None, users=_Users(), tokens=SessionTokenSigner("s"), dev_account=dev)


def test_dev_login_success_issues_token_for_dev_sub():
    it = _interactor()
    result = it.dev_login(DEV_ACCOUNT_ID, DEV_ACCOUNT_PASSWORD)
    assert result is not None
    assert result.user == SessionUserDTO(sub=DEV_SUB, email="dev@local", name="dev")
    assert it.current_user(result.session_token) == result.user
    assert it._users.saved[0].sub == DEV_SUB


@pytest.mark.parametrize("acc,pw", [
    (DEV_ACCOUNT_ID, "wrong"),
    (WRONG_ACCOUNT_ID, DEV_ACCOUNT_PASSWORD),
    ("", ""),
    (DEV_ACCOUNT_ID, WRONG_PASSWORD),
])
def test_dev_login_rejects_wrong_credentials(acc, pw):
    assert _interactor().dev_login(acc, pw) is None


def test_dev_login_disabled_without_account():
    assert _interactor(dev=None).dev_login(DEV_ACCOUNT_ID, DEV_ACCOUNT_PASSWORD) is None


def test_current_user_accepts_dev_token_when_dev_account_configured():
    it = _interactor()
    result = it.dev_login(DEV_ACCOUNT_ID, DEV_ACCOUNT_PASSWORD)
    assert it.current_user(result.session_token) == result.user


def test_current_user_rejects_dev_token_when_dev_account_not_configured():
    issuer = _interactor()
    result = issuer.dev_login(DEV_ACCOUNT_ID, DEV_ACCOUNT_PASSWORD)
    reader = _interactor(dev=None)
    assert reader.current_user(result.session_token) is None


def test_current_user_rejects_dev_token_when_account_id_changed():
    issuer = _interactor()
    result = issuer.dev_login(DEV_ACCOUNT_ID, DEV_ACCOUNT_PASSWORD)
    reader = _interactor(dev=DevAccountDTO(account_id=WRONG_ACCOUNT_ID, password=DEV_ACCOUNT_PASSWORD))
    assert reader.current_user(result.session_token) is None


def test_current_user_accepts_google_sub_when_no_dev_account_configured():
    tokens = SessionTokenSigner("s")
    google_user = SessionUserDTO(sub="google:12345", email="a@b.com", name="a")
    token = tokens.issue(google_user, 3600)
    it = AuthInteractor(oauth=None, users=_Users(), tokens=tokens, dev_account=None)
    assert it.current_user(token) == google_user


def _client(monkeypatch, dev_login="on", per_minute=5):
    from main import app
    from apps.engine.dependencies.engine_dependency import get_auth_use_case
    from apps.engine.adapter.inbound.api.v1 import guards

    monkeypatch.setattr(auth_router, "_settings", lambda: type("S", (), {
        "dev_login": dev_login, "frontend_base_url": "http://localhost:3500",
        "dev_login_per_minute": per_minute})())
    monkeypatch.setattr(guards, "_settings", lambda: type("S", (), {"trust_proxy": False, "guard_auth": "on", "auth_required": True,
        "ip_sessions_per_minute": 5, "ip_actions_per_minute": 30})())
    auth_router._DEV_LOGIN_BUCKET.clear()
    app.dependency_overrides[get_auth_use_case] = lambda: _interactor()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_auth_use_case, None)
        auth_router._DEV_LOGIN_BUCKET.clear()


@pytest.fixture
def client(monkeypatch):
    yield from _client(monkeypatch)


@pytest.fixture
def client_off(monkeypatch):
    yield from _client(monkeypatch, dev_login="off")


def test_endpoint_404_when_dev_login_off(client_off):
    assert client_off.post("/api/v1/auth/dev/login", json={"id": DEV_ACCOUNT_ID, "password": DEV_ACCOUNT_PASSWORD}).status_code == 404


def test_endpoint_401_on_wrong_password(client):
    res = client.post("/api/v1/auth/dev/login", json={"id": DEV_ACCOUNT_ID, "password": "x"})
    assert res.status_code == 401
    assert res.json() == {"detail": "아이디 또는 비밀번호가 틀렸다"}
    assert "rd_session" not in res.cookies


def test_endpoint_sets_cookie_and_me_returns_dev_user(client):
    res = client.post("/api/v1/auth/dev/login", json={"id": DEV_ACCOUNT_ID, "password": DEV_ACCOUNT_PASSWORD})
    assert res.status_code == 200
    assert res.json()["ok"] is True and res.json()["user"]["sub"] == DEV_SUB
    assert "rd_session" in res.cookies
    assert "HttpOnly" in res.headers["set-cookie"]
    assert client.get("/api/v1/auth/me").json()["sub"] == DEV_SUB


def test_endpoint_422_on_long_input(client):
    res = client.post("/api/v1/auth/dev/login", json={"id": "a" * 65, "password": DEV_ACCOUNT_PASSWORD})
    assert res.status_code == 422


def test_endpoint_422_on_long_password(client):
    res = client.post("/api/v1/auth/dev/login", json={"id": DEV_ACCOUNT_ID, "password": "a" * 65})
    assert res.status_code == 422


def test_endpoint_429_after_five_attempts_per_minute(client):
    for _ in range(5):
        assert client.post("/api/v1/auth/dev/login", json={"id": DEV_ACCOUNT_ID, "password": "x"}).status_code == 401
    res = client.post("/api/v1/auth/dev/login", json={"id": DEV_ACCOUNT_ID, "password": DEV_ACCOUNT_PASSWORD})
    assert res.status_code == 429
    assert res.json()["detail"]["detail"] == "요청이 너무 잦다"
    assert int(res.headers["Retry-After"]) >= 1
