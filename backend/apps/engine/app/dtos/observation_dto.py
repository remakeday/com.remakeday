"""Public observations: source records, never player hypotheses or hidden truth."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from apps.engine.app.dtos.scenario_dto import IllustrationDTO


class ObservationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation_id: str
    attempt_id: str
    loop_id: str
    loop_n: int
    beat: int
    scene_id: str
    scene_title: str
    actor: str | None = None
    text: str
    source_kind: Literal["scene", "image", "statement", "rule_result"]
    verification: Literal["observed", "reported"] = "observed"
    illustrations: list[IllustrationDTO] = Field(default_factory=list)
    rule_id: str | None = None
