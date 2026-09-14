from pydantic import BaseModel


class HealthModelsResponse(BaseModel):
    npc: str
    core: str
    embedding: str


class HealthResponse(BaseModel):
    scenario: str
    harness: str
    models: HealthModelsResponse
    db: str
