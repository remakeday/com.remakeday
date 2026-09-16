"""Driving Port — 인증 유즈케이스."""

from __future__ import annotations

from typing import Protocol

from apps.engine.app.dtos.auth_dto import LoginResultDTO, LoginStartDTO, SessionUserDTO


class AuthUseCase(Protocol):
    def begin_login(self) -> LoginStartDTO:
        """구글 인증 시작 — authorize URL과 state를 만든다."""
        ...

    def complete_login(self, code: str) -> LoginResultDTO:
        """콜백의 code로 로그인을 완성한다 — 프로필 교환·사용자 저장·세션 발급."""
        ...

    def current_user(self, session_token: str | None) -> SessionUserDTO | None:
        """세션 토큰에서 현재 사용자를 복원한다. 없거나 무효면 None."""
        ...
