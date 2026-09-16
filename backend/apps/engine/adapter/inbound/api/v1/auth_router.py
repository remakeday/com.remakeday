"""Auth 라우터 — 구글 OAuth 시작·콜백·현재 사용자·로그아웃.

경로는 등록된 redirect_uri(`/api/v1/auth/google/callback`)에 맞춘다.
쿠키·리다이렉트·CSRF state 검증은 이 인바운드 어댑터의 책임이고,
프로필 교환·사용자 저장·세션 발급 로직은 AuthUseCase가 맡는다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from apps.engine.app.dtos.auth_dto import SessionUserDTO
from apps.engine.app.ports.input.auth_use_case import AuthUseCase
from apps.engine.app.use_cases.auth_interactor import SESSION_TTL_SECONDS
from apps.engine.dependencies.engine_dependency import get_auth_use_case
from core.matrix.grid_keymaker_secret_manager import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SESSION_COOKIE = "rd_session"
STATE_COOKIE = "rd_oauth_state"
_STATE_TTL_SECONDS = 600


def _cookie_secure() -> bool:
    # 로컬 http(localhost)에서는 Secure 쿠키가 전송되지 않으므로 https일 때만 켠다.
    return get_settings().frontend_base_url.startswith("https://")


@router.get("/google/start")
def google_start(use_case: AuthUseCase = Depends(get_auth_use_case)) -> RedirectResponse:
    start = use_case.begin_login()
    response = RedirectResponse(start.authorize_url, status_code=307)
    response.set_cookie(
        STATE_COOKIE,
        start.state,
        max_age=_STATE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        path="/",
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    use_case: AuthUseCase = Depends(get_auth_use_case),
) -> RedirectResponse:
    frontend = get_settings().frontend_base_url.rstrip("/")
    if error or not code:
        return RedirectResponse(f"{frontend}/?login=error", status_code=307)

    # CSRF 방지 — 시작 때 심은 state 쿠키와 콜백 쿼리의 state가 일치해야 한다.
    expected_state = request.cookies.get(STATE_COOKIE)
    if not state or not expected_state or state != expected_state:
        return RedirectResponse(f"{frontend}/?login=state", status_code=307)

    try:
        result = use_case.complete_login(code)
    except Exception:  # noqa: BLE001 — 교환 실패는 전부 로그인 실패로 되돌린다
        return RedirectResponse(f"{frontend}/?login=error", status_code=307)

    response = RedirectResponse(f"{frontend}/?login=ok", status_code=307)
    response.delete_cookie(STATE_COOKIE, path="/")
    response.set_cookie(
        SESSION_COOKIE,
        result.session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        path="/",
    )
    return response


@router.get("/me")
def me(
    request: Request, use_case: AuthUseCase = Depends(get_auth_use_case)
) -> SessionUserDTO:
    user = use_case.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=401, detail="로그인되어 있지 않습니다")
    return user


@router.post("/logout")
def logout() -> JSONResponse:
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
