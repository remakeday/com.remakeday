from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    scenario = build_scenario(get_settings().scenario)
    with get_session_factory()() as session:
        ScenarioSeedInteractor(ScenarioSeedRepository(session)).sync(scenario.bundle())
    yield


app = FastAPI(title="REMAKE DAY Backend", lifespan=lifespan)
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
