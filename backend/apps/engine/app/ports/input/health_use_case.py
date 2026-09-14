from typing import Protocol

from apps.engine.app.dtos.health_dto import HealthDTO


class HealthUseCase(Protocol):
    def check(self) -> HealthDTO: ...
