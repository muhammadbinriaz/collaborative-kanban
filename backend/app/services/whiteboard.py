from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.user import User
from app.models.whiteboard import Whiteboard
from app.models.workspace import WorkspaceRole
from app.schemas.whiteboard import WhiteboardCreate, WhiteboardPublic, WhiteboardSummary, WhiteboardUpdate
from app.services.activity import log_activity
from app.services.workspace import require_workspace


def list_whiteboards(db: Session, user: User, workspace_id: UUID) -> list[WhiteboardSummary]:
    require_workspace(db, workspace_id, user)
    rows = db.scalars(
        select(Whiteboard)
        .where(Whiteboard.workspace_id == workspace_id)
        .order_by(Whiteboard.updated_at.desc())
    ).all()
    return [WhiteboardSummary.model_validate(row) for row in rows]


def create_whiteboard(
    db: Session, user: User, workspace_id: UUID, payload: WhiteboardCreate
) -> WhiteboardPublic:
    require_workspace(db, workspace_id, user, WorkspaceRole.MEMBER)
    board = Whiteboard(
        workspace_id=workspace_id,
        name=payload.name.strip(),
        scene={"elements": [], "appState": {}, "files": {}},
        created_by_id=user.id,
    )
    db.add(board)
    log_activity(
        db,
        workspace_id=workspace_id,
        actor=user,
        action="whiteboard.created",
        summary=f'{user.name} created whiteboard "{board.name}"',
    )
    db.commit()
    db.refresh(board)
    return WhiteboardPublic.model_validate(board)


def get_whiteboard(db: Session, user: User, whiteboard_id: UUID) -> WhiteboardPublic:
    board = db.get(Whiteboard, whiteboard_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Whiteboard not found")
    require_workspace(db, board.workspace_id, user)
    return WhiteboardPublic.model_validate(board)


def _active_count(elements: object) -> int:
    if not isinstance(elements, list):
        return 0
    return sum(1 for el in elements if isinstance(el, dict) and not el.get("isDeleted"))


def _element_rank(el: dict[str, Any]) -> tuple[int, int]:
    return (int(el.get("version") or 0), int(el.get("versionNonce") or 0))


def merge_scenes(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    """Excalidraw-style merge: higher version wins; never let a blank snapshot wipe the board."""
    existing = existing if isinstance(existing, dict) else {}
    incoming = incoming if isinstance(incoming, dict) else {}

    existing_elements = existing.get("elements") if isinstance(existing.get("elements"), list) else []
    incoming_elements = incoming.get("elements") if isinstance(incoming.get("elements"), list) else []

    # Blank client hydrate / race — keep stored scene.
    if _active_count(incoming_elements) == 0 and _active_count(existing_elements) > 0:
        if len(incoming_elements) == 0:
            return existing

    merged: dict[str, dict[str, Any]] = {}
    for el in existing_elements:
        if isinstance(el, dict) and el.get("id"):
            merged[str(el["id"])] = el
    for el in incoming_elements:
        if not isinstance(el, dict) or not el.get("id"):
            continue
        key = str(el["id"])
        current = merged.get(key)
        if current is None or _element_rank(el) >= _element_rank(current):
            merged[key] = el

    files: dict[str, Any] = {}
    if isinstance(existing.get("files"), dict):
        files.update(existing["files"])
    if isinstance(incoming.get("files"), dict):
        files.update(incoming["files"])

    app_state = incoming.get("appState") if isinstance(incoming.get("appState"), dict) else existing.get("appState")
    if not isinstance(app_state, dict):
        app_state = {}

    return {
        "elements": list(merged.values()),
        "appState": {
            "viewBackgroundColor": app_state.get("viewBackgroundColor"),
            "gridSize": app_state.get("gridSize"),
            "currentItemFontFamily": app_state.get("currentItemFontFamily"),
        },
        "files": files,
    }


def update_whiteboard(
    db: Session, user: User, whiteboard_id: UUID, payload: WhiteboardUpdate
) -> WhiteboardPublic:
    board = db.get(Whiteboard, whiteboard_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Whiteboard not found")
    require_workspace(db, board.workspace_id, user, WorkspaceRole.MEMBER)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        board.name = data["name"].strip()
    if "scene" in data and data["scene"] is not None:
        board.scene = merge_scenes(board.scene if isinstance(board.scene, dict) else None, data["scene"])
        flag_modified(board, "scene")
        board.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(board)
    return WhiteboardPublic.model_validate(board)


def delete_whiteboard(db: Session, user: User, whiteboard_id: UUID) -> None:
    board = db.get(Whiteboard, whiteboard_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Whiteboard not found")
    require_workspace(db, board.workspace_id, user, WorkspaceRole.MEMBER)
    workspace_id = board.workspace_id
    name = board.name
    db.delete(board)
    log_activity(
        db,
        workspace_id=workspace_id,
        actor=user,
        action="whiteboard.deleted",
        summary=f'{user.name} deleted whiteboard "{name}"',
    )
    db.commit()
