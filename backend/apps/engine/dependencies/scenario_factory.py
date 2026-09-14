"""시나리오 팩토리 — SCENARIO 스위치 해석 + scenario_a 누락 시 example 폴백."""

import logging
from functools import lru_cache

from apps.engine.app.ports.output.scenario_port import ScenarioPort

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def build_scenario(name: str) -> ScenarioPort:
    if name == "example":
        return _example()
    if name == "a":
        try:
            from apps.scenarios.scenario_a.adapter import build

            return build()
        except ImportError:
            logger.warning("scenario_a를 찾을 수 없어 scenario_example로 기동한다")
            return _example()
    if name == "audit":
        from apps.scenarios.scenario_audit.adapter import build as build_audit

        return build_audit()
    raise ValueError(f"알 수 없는 시나리오: {name}")


def _example() -> ScenarioPort:
    from apps.scenarios.scenario_example.adapter import build

    return build()
