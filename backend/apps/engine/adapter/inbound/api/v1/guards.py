"""과잉 사용 방지 의존성 — 로그인·IP 버킷·클라이언트 IP (설계: specs/2026-09-16-abuse-guard-design.md)."""

import hashlib
import ipaddress
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
from apps.engine.app.use_cases.attempt_access_interactor import (
    AttemptAccessInteractor,
    AttemptNotFound,
)
from apps.engine.dependencies.engine_dependency import get_attempt_access, get_auth_use_case
from apps.engine.domain.entities.guard_rules import TokenBucket
from core.matrix.grid_keymaker_secret_manager import get_settings
from core.matrix.grid_oracle_database_manager import get_session

SESSION_COOKIE = "rd_session"
_BUCKETS: dict[str, TokenBucket] = {}


def _settings():
    return get_settings()


def client_ip(request: Request) -> str:
    if _settings().trust_proxy:
        cf_ip = (request.headers.get("cf-connecting-ip") or "").strip()
        if cf_ip:
            try:
                ipaddress.ip_address(cf_ip)
                return cf_ip
            except ValueError:
                pass
    return request.client.host if request.client else "unknown"


def ip_hash(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:12]


def require_user(
    request: Request,
    use_case=Depends(get_auth_use_case),
    session: Session = Depends(get_session),
) -> SessionUserDTO:
    if not _settings().auth_required:
        if "cf-connecting-ip" in request.headers:
            # off는 러너용 로컬 우회다. Cloudflare(터널)를 거친 요청이면 .env 프론트 주소와 무관하게 공개 요청이므로
            # `dev`로 통과시키지 않는다. 401이면 로그인 화면으로 오해되므로(off에선 로그인이 소용없다) 403.
            EventLogRepository(session).record(
                uuid.uuid4(),
                GuardEvent(layer="auth", reason="guard_auth_off_via_proxy",
                           ip_hash=ip_hash(client_ip(request)), user_sub=None),
            )
            raise HTTPException(status_code=403, detail="인증 우회 모드는 외부 요청을 받지 않는다")
        return SessionUserDTO(sub="dev", email="", name="dev")
    user = use_case.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        EventLogRepository(session).record(
            uuid.uuid4(),
            GuardEvent(layer="auth", reason="no_session", ip_hash=ip_hash(client_ip(request)), user_sub=None),
        )
        raise HTTPException(status_code=401, detail="로그인이 필요하다")
    return user


def require_attempt_owner(
    request: Request,
    user: SessionUserDTO = Depends(require_user),
    access: AttemptAccessInteractor = Depends(get_attempt_access),
) -> None:
    """판 하위 경로(attempt_id·loop_id·night_id)의 판이 요청 사용자 것인지 — 남의 판·없는 판은 같은 404 (F26)."""
    try:
        access.ensure_owner(request.path_params, user)
    except AttemptNotFound as e:
        raise HTTPException(status_code=404, detail="판을 찾을 수 없다") from e


def ip_bucket(name: str, per_minute_attr: str):
    def dependency(request: Request, user: SessionUserDTO = Depends(require_user)) -> None:
        per_minute = max(1, getattr(_settings(), per_minute_attr))
        bucket = _BUCKETS.setdefault(name, TokenBucket(capacity=per_minute, refill_per_sec=per_minute / 60.0))
        key = f"u:{user.sub}" if _settings().auth_required else f"ip:{client_ip(request)}"
        ok, wait = bucket.take(key, now=time.monotonic())
        if not ok:
            retry = max(1, math.ceil(wait))
            raise HTTPException(status_code=429, detail={"detail": "요청이 너무 잦다", "retry_after": retry},
                                headers={"Retry-After": str(retry)})
    return dependency
