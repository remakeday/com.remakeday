from apps.engine.app.dtos.scenario_dto import ScenarioBundleDTO
from apps.engine.app.ports.output.scenario_seed_port import ScenarioSeedPort


class ScenarioSeedInteractor:
    def __init__(self, seed: ScenarioSeedPort) -> None:
        self._seed = seed

    def sync(self, bundle: ScenarioBundleDTO) -> None:
        self._seed.upsert_bundle(bundle)
