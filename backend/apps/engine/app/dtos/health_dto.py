from pydantic import BaseModel, ConfigDict


class HealthDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    db: str  # ok | error
