"""과잉 사용 방지 의존성 — 로그인·IP 버킷·클라이언트 IP (설계: specs/2026-09-16-abuse-guard-design.md)."""

import hashlib
import math
import time
import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.app.dtos.auth_dto import SessionUserDTO
from apps.engine.app.dtos.event_log_dto import GuardEvent
from apps.engine.dependencies.engine_dependency import get_auth_use_case
from apps.engine.domain.entities.guard_rules import TokenBucket
from core.matrix.grid_keymaker_secret_manager import get_settings
from core.matrix.grid_oracle_database_manager import get_session

SESSION_COOKIE = "rd_session"
_BUCKETS: dict[str, TokenBucket] = {}


def _settings():
    return get_settings()


def client_ip(request: Request) -> str:
    if _settings().trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ip_hash(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:12]


def require_user(
    request: Request,
    use_case=Depends(get_auth_use_case),
    session: Session = Depends(get_session),
) -> SessionUserDTO:
    if _settings().guard_auth == "off":
        return SessionUserDTO(sub="dev", email="", name="dev")
    user = use_case.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        EventLogRepository(session).record(
            uuid.uuid4(),
            GuardEvent(layer="auth", reason="no_session", ip_hash=ip_hash(client_ip(request)), user_sub=None),
        )
        raise HTTPException(status_code=401, detail="로그인이 필요하다")
    return user


def ip_bucket(name: str, per_minute_attr: str):
    def dependency(request: Request, user: SessionUserDTO = Depends(require_user)) -> None:
        per_minute = max(1, getattr(_settings(), per_minute_attr))
        bucket = _BUCKETS.setdefault(name, TokenBucket(capacity=per_minute, refill_per_sec=per_minute / 60.0))
        key = f"u:{user.sub}" if _settings().guard_auth != "off" else f"ip:{client_ip(request)}"
        ok, wait = bucket.take(key, now=time.monotonic())
        if not ok:
            retry = max(1, math.ceil(wait))
            raise HTTPException(status_code=429, detail={"detail": "요청이 너무 잦다", "retry_after": retry},
                                headers={"Retry-After": str(retry)})
    return dependency
