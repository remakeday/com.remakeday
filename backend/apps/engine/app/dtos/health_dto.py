from pydantic import BaseModel, ConfigDict


class HealthModelsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    npc: str
    core: str  # Planner·Advisor·Normalizer·Manager·Evaluator
    embedding: str


class HealthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str
    harness: str  # on | off
    models: HealthModelsDTO
    db: str  # ok | error
