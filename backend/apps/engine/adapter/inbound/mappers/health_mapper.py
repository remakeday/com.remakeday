from apps.engine.adapter.inbound.api.schemas.health_schema import HealthResponse
from apps.engine.app.dtos.health_dto import HealthDTO


class HealthMapper:
    @staticmethod
    def to_response(dto: HealthDTO) -> HealthResponse:
        return HealthResponse(db=dto.db)
