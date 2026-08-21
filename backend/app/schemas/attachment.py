from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttachmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_id: UUID
    uploaded_by_id: UUID | None
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    download_url: str | None = None
