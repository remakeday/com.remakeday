"""Auth 경계 DTO — 구글 프로필·세션 사용자·로그인 시작 결과."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleProfileDTO:
    """구글 토큰 교환으로 얻은 계정 프로필."""

    sub: str
    email: str
    name: str
    picture: str = ""


@dataclass(frozen=True)
class SessionUserDTO:
    """세션 쿠키에 담기고 /auth/me가 돌려주는 사용자."""

    sub: str
    email: str
    name: str
    picture: str = ""


@dataclass(frozen=True)
class LoginStartDTO:
    """구글 인증 화면으로 보낼 URL과, CSRF 방지용 state."""

    authorize_url: str
    state: str


@dataclass(frozen=True)
class LoginResultDTO:
    """콜백 처리 결과 — 세션 토큰과 사용자."""

    session_token: str
    user: SessionUserDTO
