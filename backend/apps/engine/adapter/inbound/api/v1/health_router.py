from fastapi import APIRouter, Depends

from apps.engine.adapter.inbound.api.schemas.health_schema import HealthResponse
from apps.engine.adapter.inbound.mappers.health_mapper import HealthMapper
from apps.engine.app.ports.input.health_use_case import HealthUseCase
from apps.engine.dependencies.engine_dependency import get_health_use_case

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(use_case: HealthUseCase = Depends(get_health_use_case)) -> HealthResponse:
    return HealthMapper.to_response(use_case.check())
