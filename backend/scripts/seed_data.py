"""Seed a demo user, workspace, board, and cards."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Allow `python scripts/seed_data.py` from /app in Docker and from backend/ locally.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.board import Board
from app.models.card import Card, Label
from app.models.list import BoardList
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.board import DEFAULT_LABELS, DEFAULT_LISTS

DEMO_EMAIL = "demo@kanban.dev"
DEMO_PASSWORD = "Demo12345!"


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if existing:
            print("Demo data already exists. Login with demo@kanban.dev / Demo12345!")
            return

        user = User(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            name="Demo User",
            email_verified=True,
        )
        db.add(user)
        db.flush()

        workspace = Workspace(name="Acme Product", slug="acme-product-demo", owner_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER.value))

        board = Board(
            workspace_id=workspace.id,
            name="Sprint Board",
            description="Demo board for the AI Kanban Phase 1 core.",
            position=65535,
        )
        db.add(board)
        db.flush()

        lists: list[BoardList] = []
        for index, name in enumerate(DEFAULT_LISTS):
            board_list = BoardList(board_id=board.id, name=name, position=(index + 1) * 65535.0)
            db.add(board_list)
            lists.append(board_list)
        db.flush()

        labels: list[Label] = []
        for name, color in DEFAULT_LABELS:
            label = Label(board_id=board.id, name=name, color=color)
            db.add(label)
            labels.append(label)
        db.flush()

        now = datetime.now(UTC)
        cards = [
            Card(
                list_id=lists[0].id,
                title="Design workspace switcher",
                description="Allow users to jump between workspaces from the header.",
                position=65535,
                due_date=now + timedelta(days=3),
                assignee_id=user.id,
            ),
            Card(
                list_id=lists[0].id,
                title="Add card due-date picker",
                description="Support setting and clearing due dates from the card modal.",
                position=131070,
                assignee_id=user.id,
            ),
            Card(
                list_id=lists[1].id,
                title="Implement drag-and-drop moves",
                description="Persist card position and list_id via POST /cards/{id}/move.",
                position=65535,
                assignee_id=user.id,
            ),
            Card(
                list_id=lists[2].id,
                title="Custom JWT authentication",
                description="Access tokens plus rotating refresh cookies.",
                position=65535,
                assignee_id=user.id,
            ),
        ]
        for card in cards:
            db.add(card)
        db.flush()
        cards[0].labels = [labels[1]]
        cards[1].labels = [labels[2]]
        cards[2].labels = [labels[3]]
        cards[3].labels = [labels[2]]
        db.commit()
        print("Seeded demo user demo@kanban.dev / Demo12345!")
        print(f"Workspace: {workspace.name} ({workspace.id})")
        print(f"Board: {board.name} ({board.id})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
