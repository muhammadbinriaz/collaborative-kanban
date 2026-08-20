from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    position: float | None = None


class ListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    position: float | None = None


class ListPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_id: UUID
    name: str
    position: float
    created_at: datetime
    updated_at: datetime
