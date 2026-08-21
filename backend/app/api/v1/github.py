from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.github import GithubConnectionPublic, GithubRepoUpdate, GithubStatus
from app.services import github as github_service

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/workspaces/{workspace_id}/status", response_model=GithubStatus)
def github_status(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> GithubStatus:
    return github_service.status_for_workspace(db, current_user, workspace_id)


@router.get("/workspaces/{workspace_id}/authorize")
def github_authorize(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> dict[str, str]:
    return {"authorize_url": github_service.authorize_url(db, current_user, workspace_id)}


@router.get("/callback")
async def github_callback(
    db: DbSession,
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    workspace_id, _ = await github_service.handle_oauth_callback(db, code=code, state=state)
    return RedirectResponse(f"{settings.FRONTEND_URL}/workspaces/{workspace_id}?github=connected")


@router.put("/workspaces/{workspace_id}/repo", response_model=GithubConnectionPublic)
def set_repo(
    workspace_id: UUID, payload: GithubRepoUpdate, db: DbSession, current_user: CurrentUser
) -> GithubConnectionPublic:
    return github_service.set_repo(db, current_user, workspace_id, payload)


@router.delete("/workspaces/{workspace_id}", status_code=204)
def disconnect(workspace_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    github_service.disconnect(db, current_user, workspace_id)
    return Response(status_code=204)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    db: DbSession,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
) -> dict:
    body = await request.body()
    return await github_service.handle_webhook(
        db,
        body=body,
        event=x_github_event,
        signature=x_hub_signature_256,
        delivery=x_github_delivery,
    )
