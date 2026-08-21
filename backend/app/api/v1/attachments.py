from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession
from app.schemas.attachment import AttachmentPublic
from app.services import attachment as attachment_service

router = APIRouter(tags=["attachments"])


@router.get("/cards/{card_id}/attachments", response_model=list[AttachmentPublic])
def list_attachments(card_id: UUID, db: DbSession, current_user: CurrentUser) -> list[AttachmentPublic]:
    return attachment_service.list_attachments(db, current_user, card_id)


@router.post("/cards/{card_id}/attachments", response_model=AttachmentPublic, status_code=201)
async def upload_attachment(
    card_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> AttachmentPublic:
    return await attachment_service.upload_attachment(db, current_user, card_id, file)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: UUID, db: DbSession, current_user: CurrentUser
) -> Response:
    await attachment_service.delete_attachment(db, current_user, attachment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
