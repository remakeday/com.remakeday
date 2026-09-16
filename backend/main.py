from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.engine.adapter.inbound.api.v1.auth_router import router as auth_router
from apps.engine.adapter.inbound.api.v1.game_router import router as game_router
from apps.engine.adapter.inbound.api.v1.health_router import router as health_router
from apps.engine.adapter.outbound.repositories.scenario_seed_repository import (
    ScenarioSeedRepository,
)
from apps.engine.app.use_cases.scenario_seed_interactor import ScenarioSeedInteractor
from apps.engine.dependencies.scenario_factory import build_scenario
from core.matrix.grid_keymaker_secret_manager import get_settings
from core.matrix.grid_oracle_database_manager import get_session_factory


_MAX_BODY_BYTES = 262144


class MaxBodySizeMiddleware:
    """Content-Length가 상한을 넘는 요청 본문을 파싱 전에 413으로 거부한다."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            content_length = dict(scope.get("headers") or []).get(b"content-length")
            if content_length is not None:
                try:
                    too_big = int(content_length) > _MAX_BODY_BYTES
                except ValueError:
                    too_big = False
                if too_big:
                    response = JSONResponse(status_code=413, content={"detail": "요청이 너무 크다"})
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.guard_auth == "on" and settings.session_secret == "dev-session-secret-change-me":
        raise RuntimeError("SESSION_SECRET must be set when GUARD_AUTH=on")
    scenario = build_scenario(settings.scenario)
    with get_session_factory()() as session:
        ScenarioSeedInteractor(ScenarioSeedRepository(session)).sync(scenario.bundle())
    yield


app = FastAPI(title="REMAKE DAY Backend", lifespan=lifespan)
app.add_middleware(MaxBodySizeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://remakeday.com",
        "https://www.remakeday.com",
        "http://localhost:3500",
        "http://127.0.0.1:3500",
    ],
    allow_credentials=True,  # 세션 쿠키를 주고받으려면 필요(와일드카드 오리진과 병용 불가)
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(game_router)
app.include_router(auth_router)
