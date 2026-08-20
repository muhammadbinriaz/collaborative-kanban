"""phase 3 sprints and estimates

Revision ID: 003_sprints
Revises: 002_collaboration
Create Date: 2026-08-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_sprints"
down_revision: Union[str, None] = "002_collaboration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("boards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sprints_board_id", "sprints", ["board_id"])

    op.add_column("cards", sa.Column("estimate_points", sa.Float(), nullable=True))
    op.add_column(
        "cards",
        sa.Column("sprint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("cards", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_cards_sprint_id", "cards", ["sprint_id"])


def downgrade() -> None:
    op.drop_index("ix_cards_sprint_id", table_name="cards")
    op.drop_column("cards", "completed_at")
    op.drop_column("cards", "sprint_id")
    op.drop_column("cards", "estimate_points")
    op.drop_table("sprints")
