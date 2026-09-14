from typing import Protocol

from apps.engine.app.dtos.scenario_dto import ScenarioBundleDTO


class ScenarioSeedUseCase(Protocol):
    def sync(self, bundle: ScenarioBundleDTO) -> None:
        """매 기동 시 호출. upsert + 시드에서 사라진 행 정리 (early-return 금지)."""
        ...
