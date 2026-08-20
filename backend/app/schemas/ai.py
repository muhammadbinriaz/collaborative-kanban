from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AiActionRequest(BaseModel):
    card_id: UUID | None = None
    capacity_points: float | None = Field(default=None, ge=1, le=200)


class AiJobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_id: UUID
    job_type: str
    status: str
    result: dict | None = None
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


class AiStatus(BaseModel):
    groq_configured: bool
    model: str
    embeddings: str
