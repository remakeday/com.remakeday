"""AuthInteractor — 로그인 흐름을 조율한다. 포트에만 의존(프레임워크 무의존)."""

from __future__ import annotations

import secrets

from apps.engine.app.dtos.auth_dto import (
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
    ) -> None:
        self._oauth = oauth
        self._users = users
        self._tokens = tokens

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
