"""GoogleOAuthClient — 구글 OAuth 2.0 authorization code flow. OAuthClientPort 구현.

새 의존성 없이 httpx(이미 사용 중)로 토큰을 교환하고, id_token 페이로드에서
프로필을 읽는다. id_token은 구글 토큰 엔드포인트와의 TLS 직통 교환으로 받으므로
서버 측 코드 흐름에서는 별도 서명 검증 없이 신뢰한다(구글 공식 가이드 허용 범위).
"""

from __future__ import annotations

import base64
import binascii
import json
from urllib.parse import urlencode

import httpx

from apps.engine.app.dtos.auth_dto import GoogleProfileDTO

_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_SCOPES = "openid email profile"


def _decode_id_token_payload(id_token: str) -> dict:
    try:
        payload_b64 = id_token.split(".")[1]
        padding = "=" * (-len(payload_b64) % 4)
        raw = base64.urlsafe_b64decode(payload_b64 + padding)
        return json.loads(raw)
    except (IndexError, binascii.Error, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("구글 id_token을 해석할 수 없습니다") from exc


class GoogleOAuthClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def authorize_url(self, state: str) -> str:
        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "scope": _SCOPES,
                "state": state,
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        return f"{_AUTHORIZE_ENDPOINT}?{query}"

    def exchange_code(self, code: str) -> GoogleProfileDTO:
        response = httpx.post(
            _TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": self._redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        id_token = response.json().get("id_token")
        if not id_token:
            raise ValueError("토큰 응답에 id_token이 없습니다")
        claims = _decode_id_token_payload(id_token)
        return GoogleProfileDTO(
            sub=str(claims["sub"]),
            email=str(claims.get("email", "")),
            name=str(claims.get("name", "")),
            picture=str(claims.get("picture", "")),
        )
