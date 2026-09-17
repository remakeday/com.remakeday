from pydantic import BaseModel


class HealthResponse(BaseModel):
    db: str
