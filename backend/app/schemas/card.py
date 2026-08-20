from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import UserPublic
from app.schemas.board import LabelPublic


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    estimate_points: float | None = Field(default=None, ge=0, le=100)
    sprint_id: UUID | None = None
    position: float | None = None
    label_ids: list[UUID] = []


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    estimate_points: float | None = Field(default=None, ge=0, le=100)
    sprint_id: UUID | None = None
    label_ids: list[UUID] | None = None


class CardMove(BaseModel):
    list_id: UUID
    position: float


class CardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    list_id: UUID
    title: str
    description: str | None
    position: float
    due_date: datetime | None
    assignee_id: UUID | None
    estimate_points: float | None = None
    sprint_id: UUID | None = None
    completed_at: datetime | None = None
    assignee: UserPublic | None = None
    labels: list[LabelPublic] = []
    created_at: datetime
    updated_at: datetime


class ListWithCards(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_id: UUID
    name: str
    position: float
    created_at: datetime
    updated_at: datetime
    cards: list[CardPublic] = []


class BoardDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    position: float
    created_at: datetime
    updated_at: datetime
    lists: list[ListWithCards] = []
    labels: list[LabelPublic] = []
