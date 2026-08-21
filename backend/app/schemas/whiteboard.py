from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WhiteboardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WhiteboardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    scene: dict[str, Any] | None = None


class WhiteboardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    scene: dict[str, Any] | None = None
    created_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class WhiteboardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
