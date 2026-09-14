from typing import Protocol

from apps.engine.app.dtos.scenario_dto import ScenarioBundleDTO


class ScenarioSeedPort(Protocol):
    def upsert_bundle(self, bundle: ScenarioBundleDTO) -> None: ...
