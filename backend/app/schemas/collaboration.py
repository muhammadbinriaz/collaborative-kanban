from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.workspace import WorkspaceRole
from app.schemas.auth import UserPublic


class InviteCreate(BaseModel):
    role: WorkspaceRole = WorkspaceRole.MEMBER
    expires_in_hours: int = Field(default=168, ge=1, le=720)
    email: EmailStr | None = None


class InvitePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    token: str
    role: WorkspaceRole
    email: str | None = None
    expires_at: datetime
    created_at: datetime
    invite_url: str | None = None


class InvitePreview(BaseModel):
    workspace_id: UUID
    workspace_name: str
    role: WorkspaceRole
    expires_at: datetime


class InviteAcceptResponse(BaseModel):
    workspace_id: UUID
    role: WorkspaceRole


class MemberRoleUpdate(BaseModel):
    role: WorkspaceRole


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_id: UUID
    author_id: UUID
    author: UserPublic
    body: str
    mentioned_user_ids: list[UUID] = []
    created_at: datetime
    updated_at: datetime


class ActivityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    board_id: UUID | None
    card_id: UUID | None
    actor_id: UUID
    actor: UserPublic
    action: str
    summary: str
    meta: dict | None = None
    created_at: datetime


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    body: str
    link: str | None
    meta: dict | None = None
    read_at: datetime | None
    created_at: datetime
