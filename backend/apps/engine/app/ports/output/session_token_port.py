"""Driven Port — 세션 토큰 발급·검증(서명된 쿠키 값)."""

from __future__ import annotations

from typing import Protocol

from apps.engine.app.dtos.auth_dto import SessionUserDTO


class SessionTokenPort(Protocol):
    def issue(self, user: SessionUserDTO, ttl_seconds: int) -> str:
        """사용자 정보를 담아 서명된 토큰 문자열을 만든다."""
        ...

    def verify(self, token: str) -> SessionUserDTO | None:
        """서명·만료를 검증하고 사용자를 돌려준다. 위조·만료면 None."""
        ...
