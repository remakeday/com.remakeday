"""과잉 사용 방지 의존성 — 로그인·IP 버킷·클라이언트 IP (설계: specs/2026-09-16-abuse-guard-design.md)."""

import hashlib
import math
import time

from fastapi import Depends, HTTPException, Request

from apps.engine.app.dtos.auth_dto import SessionUserDTO
from apps.engine.dependencies.engine_dependency import get_auth_use_case
from apps.engine.domain.entities.guard_rules import TokenBucket
from core.matrix.grid_keymaker_secret_manager import get_settings

SESSION_COOKIE = "rd_session"
_BUCKETS: dict[str, TokenBucket] = {}


def _settings():
    return get_settings()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ip_hash(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:12]


def require_user(request: Request, use_case=Depends(get_auth_use_case)) -> SessionUserDTO:
    if _settings().guard_auth == "off":
        return SessionUserDTO(sub="dev", email="", name="dev")
    user = use_case.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요하다")
    return user


def ip_bucket(name: str, per_minute_attr: str):
    def dependency(request: Request) -> None:
        per_minute = getattr(_settings(), per_minute_attr)
        bucket = _BUCKETS.setdefault(name, TokenBucket(capacity=per_minute, refill_per_sec=per_minute / 60.0))
        ok, wait = bucket.take(client_ip(request), now=time.monotonic())
        if not ok:
            retry = max(1, math.ceil(wait))
            raise HTTPException(status_code=429, detail={"detail": "요청이 너무 잦다", "retry_after": retry},
                                headers={"Retry-After": str(retry)})
    return dependency
