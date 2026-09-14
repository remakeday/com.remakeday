from apps.engine.adapter.inbound.api.schemas.health_schema import (
    HealthModelsResponse,
    HealthResponse,
)
from apps.engine.app.dtos.health_dto import HealthDTO


class HealthMapper:
    @staticmethod
    def to_response(dto: HealthDTO) -> HealthResponse:
        return HealthResponse(
            scenario=dto.scenario,
            harness=dto.harness,
            models=HealthModelsResponse(**dto.models.model_dump()),
            db=dto.db,
        )
