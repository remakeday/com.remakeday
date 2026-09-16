"""AuthInteractor — 로그인 흐름을 조율한다. 포트에만 의존(프레임워크 무의존)."""

from __future__ import annotations

import hmac
import secrets

from apps.engine.app.dtos.auth_dto import (
    DevAccountDTO,
    GoogleProfileDTO,
    LoginResultDTO,
    LoginStartDTO,
    SessionUserDTO,
)
from apps.engine.app.ports.output.oauth_client_port import OAuthClientPort
from apps.engine.app.ports.output.session_token_port import SessionTokenPort
from apps.engine.app.ports.output.user_repository_port import UserRepositoryPort

# 세션 유효기간 — 14일
SESSION_TTL_SECONDS = 14 * 24 * 60 * 60


class AuthInteractor:
    def __init__(
        self,
        oauth: OAuthClientPort,
        users: UserRepositoryPort,
        tokens: SessionTokenPort,
        dev_account: DevAccountDTO | None = None,
    ) -> None:
        self._oauth = oauth
        self._users = users
        self._tokens = tokens
        self._dev_account = dev_account

    def begin_login(self) -> LoginStartDTO:
        state = secrets.token_urlsafe(24)
        return LoginStartDTO(authorize_url=self._oauth.authorize_url(state), state=state)

    def complete_login(self, code: str) -> LoginResultDTO:
        profile = self._oauth.exchange_code(code)
        user = self._users.upsert_from_google(profile)
        session_user = SessionUserDTO(
            sub=user.google_sub, email=user.email, name=user.name, picture=user.picture
        )
        token = self._tokens.issue(session_user, SESSION_TTL_SECONDS)
        return LoginResultDTO(session_token=token, user=session_user)

    def current_user(self, session_token: str | None) -> SessionUserDTO | None:
        if not session_token:
            return None
        return self._tokens.verify(session_token)

    def dev_login(self, account_id: str, password: str) -> LoginResultDTO | None:
        dev = self._dev_account
        if dev is None:
            return None
        id_ok = hmac.compare_digest(account_id.encode("utf-8"), dev.account_id.encode("utf-8"))
        pw_ok = hmac.compare_digest(password.encode("utf-8"), dev.password.encode("utf-8"))
        if not (id_ok and pw_ok):
            return None
        sub = f"dev:{dev.account_id}"
        self._users.upsert_from_google(GoogleProfileDTO(sub=sub, email="dev@local", name="dev"))
        session_user = SessionUserDTO(sub=sub, email="dev@local", name="dev")
        return LoginResultDTO(session_token=self._tokens.issue(session_user, SESSION_TTL_SECONDS), user=session_user)
