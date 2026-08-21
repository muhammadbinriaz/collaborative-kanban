from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.board import Board
from app.models.github import GithubConnection
from app.models.list import BoardList
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.github import GithubConnectionPublic, GithubRepoUpdate, GithubStatus
from app.services.activity import create_notification, log_activity
from app.services.workspace import require_workspace

logger = logging.getLogger(__name__)

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_API = "https://api.github.com"


def github_oauth_configured() -> bool:
    return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)


def _sign_state(payload: dict) -> str:
    raw = urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(settings.JWT_SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def _verify_state(state: str) -> dict:
    try:
        raw, sig = state.rsplit(".", 1)
        expected = hmac.new(settings.JWT_SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            raise ValueError("bad signature")
        pad = "=" * (-len(raw) % 4)
        payload = json.loads(urlsafe_b64decode(raw + pad).decode())
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc


def _public(row: GithubConnection) -> GithubConnectionPublic:
    return GithubConnectionPublic(
        id=row.id,
        workspace_id=row.workspace_id,
        installation_login=row.installation_login,
        repo_full_name=row.repo_full_name,
        created_at=row.created_at,
        updated_at=row.updated_at,
        configured=True,
    )


def status_for_workspace(db: Session, user: User, workspace_id: UUID) -> GithubStatus:
    require_workspace(db, workspace_id, user)
    row = db.scalar(select(GithubConnection).where(GithubConnection.workspace_id == workspace_id))
    return GithubStatus(
        oauth_configured=github_oauth_configured(),
        connection=_public(row) if row else None,
    )


def authorize_url(db: Session, user: User, workspace_id: UUID) -> str:
    if not github_oauth_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub OAuth is not configured")
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    state = _sign_state(
        {
            "workspace_id": str(workspace_id),
            "user_id": str(user.id),
            "exp": int(time.time()) + 600,
            "nonce": secrets.token_urlsafe(8),
        }
    )
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": f"{settings.API_URL}/api/v1/github/callback",
        "scope": "repo read:user",
        "state": state,
    }
    return f"{GITHUB_AUTHORIZE}?{urlencode(params)}"


async def handle_oauth_callback(db: Session, *, code: str, state: str) -> tuple[UUID, GithubConnectionPublic]:
    if not github_oauth_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub OAuth is not configured")
    payload = _verify_state(state)
    workspace_id = UUID(payload["workspace_id"])
    user = db.get(User, UUID(payload["user_id"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth user missing")
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)

    async with httpx.AsyncClient(timeout=30.0) as client:
        token_resp = await client.post(
            GITHUB_TOKEN,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{settings.API_URL}/api/v1/github/callback",
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token exchange failed")

        user_resp = await client.get(
            f"{GITHUB_API}/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        profile = user_resp.json()
        login = profile.get("login") or "github-user"

    row = db.scalar(select(GithubConnection).where(GithubConnection.workspace_id == workspace_id))
    if row is None:
        row = GithubConnection(
            workspace_id=workspace_id,
            connected_by_id=user.id,
            installation_login=login,
            access_token=access_token,
            webhook_secret=settings.GITHUB_WEBHOOK_SECRET or secrets.token_urlsafe(24),
        )
        db.add(row)
    else:
        row.connected_by_id = user.id
        row.installation_login = login
        row.access_token = access_token
        if not row.webhook_secret:
            row.webhook_secret = settings.GITHUB_WEBHOOK_SECRET or secrets.token_urlsafe(24)

    log_activity(
        db,
        workspace_id=workspace_id,
        actor=user,
        action="github.connected",
        summary=f"{user.name} connected GitHub as {login}",
    )
    db.commit()
    db.refresh(row)
    return workspace_id, _public(row)


def set_repo(db: Session, user: User, workspace_id: UUID, payload: GithubRepoUpdate) -> GithubConnectionPublic:
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    row = db.scalar(select(GithubConnection).where(GithubConnection.workspace_id == workspace_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connect GitHub first")
    row.repo_full_name = payload.repo_full_name.strip()
    db.commit()
    db.refresh(row)
    return _public(row)


def disconnect(db: Session, user: User, workspace_id: UUID) -> None:
    require_workspace(db, workspace_id, user, WorkspaceRole.ADMIN)
    row = db.scalar(select(GithubConnection).where(GithubConnection.workspace_id == workspace_id))
    if row:
        db.delete(row)
        db.commit()


def _verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", signature_header)


async def handle_webhook(
    db: Session,
    *,
    body: bytes,
    event: str | None,
    signature: str | None,
    delivery: str | None,
) -> dict:
    connections = db.scalars(select(GithubConnection)).all()
    matched: GithubConnection | None = None
    for conn in connections:
        secret = conn.webhook_secret or settings.GITHUB_WEBHOOK_SECRET
        if secret and _verify_signature(secret, body, signature):
            matched = conn
            break
    if matched is None and settings.GITHUB_WEBHOOK_SECRET and _verify_signature(
        settings.GITHUB_WEBHOOK_SECRET, body, signature
    ):
        matched = connections[0] if connections else None
    if matched is None:
        if not settings.GITHUB_WEBHOOK_SECRET and all(not c.webhook_secret for c in connections):
            matched = connections[0] if connections else None
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
    if matched is None:
        return {"ok": True, "ignored": "no connection"}

    payload = json.loads(body.decode("utf-8") or "{}")
    repo = (payload.get("repository") or {}).get("full_name")
    if matched.repo_full_name and repo and repo.lower() != matched.repo_full_name.lower():
        return {"ok": True, "ignored": "repo mismatch"}

    summary = None
    if event == "pull_request":
        pr = payload.get("pull_request") or {}
        action = payload.get("action")
        title = pr.get("title") or "PR"
        number = pr.get("number")
        summary = f"GitHub PR #{number} {action}: {title}"
        await _maybe_notify_cards(db, matched.workspace_id, text=f"{title} {pr.get('body') or ''}", note=summary)
    elif event == "push":
        commits = payload.get("commits") or []
        summary = f"GitHub push ({len(commits)} commits) on {payload.get('ref')}"
        for commit in commits[:10]:
            message = commit.get("message") or ""
            await _maybe_notify_cards(
                db,
                matched.workspace_id,
                text=message,
                note=f"Commit: {message.splitlines()[0][:120]}",
            )
    elif event == "issues":
        issue = payload.get("issue") or {}
        action = payload.get("action")
        summary = f"GitHub issue #{issue.get('number')} {action}: {issue.get('title')}"

    if summary:
        actor = db.get(User, matched.connected_by_id) if matched.connected_by_id else None
        if actor:
            log_activity(
                db,
                workspace_id=matched.workspace_id,
                actor=actor,
                action=f"github.{event or 'event'}",
                summary=summary,
                meta={"delivery": delivery, "repo": repo},
            )
            db.commit()
    return {"ok": True, "event": event}


async def _maybe_notify_cards(db: Session, workspace_id: UUID, *, text: str, note: str) -> None:
    boards = db.scalars(select(Board).where(Board.workspace_id == workspace_id)).all()
    lowered = text.lower()
    for board in boards:
        lists = db.scalars(
            select(BoardList).options(selectinload(BoardList.cards)).where(BoardList.board_id == board.id)
        ).all()
        for board_list in lists:
            for card in board_list.cards:
                needle = card.title.lower().strip()
                if len(needle) >= 6 and needle in lowered:
                    members = db.scalars(
                        select(User)
                        .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
                        .where(WorkspaceMember.workspace_id == workspace_id)
                    ).all()
                    for member in members:
                        create_notification(
                            db,
                            user_id=member.id,
                            type="github",
                            title="GitHub linked activity",
                            body=note,
                            link=f"/boards/{board.id}",
                            meta={"card_id": str(card.id)},
                        )
                    return
