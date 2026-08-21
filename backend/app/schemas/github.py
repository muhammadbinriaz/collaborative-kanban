from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GithubConnectionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    installation_login: str
    repo_full_name: str | None
    created_at: datetime
    updated_at: datetime
    configured: bool = True


class GithubRepoUpdate(BaseModel):
    repo_full_name: str = Field(min_length=3, max_length=255)


class GithubStatus(BaseModel):
    oauth_configured: bool
    connection: GithubConnectionPublic | None = None
