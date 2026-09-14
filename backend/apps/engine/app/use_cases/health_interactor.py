from collections.abc import Callable

from apps.engine.app.dtos.health_dto import HealthDTO, HealthModelsDTO
from apps.engine.app.ports.output.scenario_port import ScenarioPort


class HealthInteractor:
    def __init__(
        self,
        scenario: ScenarioPort,
        harness: str,
        models: HealthModelsDTO,
        db_ping: Callable[[], bool],
    ) -> None:
        self._scenario = scenario
        self._harness = harness
        self._models = models
        self._db_ping = db_ping

    def check(self) -> HealthDTO:
        try:
            db = "ok" if self._db_ping() else "error"
        except Exception:
            db = "error"
        return HealthDTO(
            scenario=self._scenario.name(),
            harness=self._harness,
            models=self._models,
            db=db,
        )
