from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    goal: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class SprintUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    goal: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class SprintPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_id: UUID
    name: str
    goal: str | None
    status: str
    start_date: datetime | None
    end_date: datetime | None
    created_at: datetime
    updated_at: datetime
    total_points: float = 0
    completed_points: float = 0
    card_count: int = 0


class SprintCardAssign(BaseModel):
    card_ids: list[UUID]


class BurndownPoint(BaseModel):
    date: str
    ideal_remaining: float
    actual_remaining: float | None = None


class VelocityPoint(BaseModel):
    sprint_id: UUID
    sprint_name: str
    completed_points: float
    committed_points: float


class WorkloadPoint(BaseModel):
    user_id: UUID | None
    user_name: str
    card_count: int
    estimate_points: float


class BottleneckInsight(BaseModel):
    type: str
    title: str
    detail: str
    severity: str
    meta: dict | None = None


class BoardAnalytics(BaseModel):
    burndown: list[BurndownPoint]
    velocity: list[VelocityPoint]
    workload: list[WorkloadPoint]
    bottlenecks: list[BottleneckInsight]
    active_sprint: SprintPublic | None = None
