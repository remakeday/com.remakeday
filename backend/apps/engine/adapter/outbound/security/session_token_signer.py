"""SessionTokenSigner — HMAC-SHA256으로 서명된 세션 토큰. SessionTokenPort 구현.

새 의존성 없이 stdlib만 사용한다. 토큰 형식: base64url(payload_json).base64url(hmac).
payload에는 sub·email·name·picture와 만료(exp, epoch초)가 들어간다.
비밀은 서버만 알므로 위조가 불가하고, 클라이언트는 값을 읽을 수 있으나 바꿀 수 없다.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time

from apps.engine.app.dtos.auth_dto import SessionUserDTO


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class SessionTokenSigner:
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def _sign(self, payload_b64: str) -> str:
        digest = hmac.new(self._secret, payload_b64.encode("ascii"), hashlib.sha256).digest()
        return _b64e(digest)

    def issue(self, user: SessionUserDTO, ttl_seconds: int) -> str:
        payload = {
            "sub": user.sub,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "exp": int(time.time()) + ttl_seconds,
        }
        payload_b64 = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return f"{payload_b64}.{self._sign(payload_b64)}"

    def verify(self, token: str) -> SessionUserDTO | None:
        try:
            payload_b64, signature = token.split(".", 1)
        except ValueError:
            return None
        if not hmac.compare_digest(signature, self._sign(payload_b64)):
            return None
        try:
            payload = json.loads(_b64d(payload_b64))
        except (binascii.Error, json.JSONDecodeError, ValueError):
            return None
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return SessionUserDTO(
            sub=str(payload.get("sub", "")),
            email=str(payload.get("email", "")),
            name=str(payload.get("name", "")),
            picture=str(payload.get("picture", "")),
        )
