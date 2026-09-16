"""Driven Port — 외부 OAuth 제공자(구글)와의 협업 인터페이스."""

from __future__ import annotations

from typing import Protocol

from apps.engine.app.dtos.auth_dto import GoogleProfileDTO


class OAuthClientPort(Protocol):
    def authorize_url(self, state: str) -> str:
        """사용자를 보낼 제공자 인증 화면 URL. state는 CSRF 방지용으로 그대로 실린다."""
        ...

    def exchange_code(self, code: str) -> GoogleProfileDTO:
        """authorization code를 토큰으로 교환하고 계정 프로필을 돌려준다."""
        ...
