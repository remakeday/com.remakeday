"""이어하기 라우터 — 로그인 사용자 자신의 진행 중인 판 (설계 2026-10-16 §2.2·§2.3).

경로에 판 ID가 없으므로 판 주인 확인(require_attempt_owner) 대신 로그인(require_user)만 건다.
대상 판은 세션 사용자의 판 중에서만 고른다 — 남의 판은 애초에 후보가 아니다.
"""

from fastapi import APIRouter, Depends, Response

from apps.engine.adapter.inbound.api.v1.guards import require_user
from apps.engine.dependencies.engine_dependency import get_resume_interactor

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get("/attempts/active")
def active_attempt(user=Depends(require_user), uc=Depends(get_resume_interactor)):
    return uc.active(user)


@router.post("/attempts/active/abandon", status_code=204)
def abandon_active_attempt(user=Depends(require_user), uc=Depends(get_resume_interactor)) -> Response:
    uc.abandon(user)
    return Response(status_code=204)
