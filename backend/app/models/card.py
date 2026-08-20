from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

card_labels = Table(
    "card_labels",
    Base.metadata,
    Column("card_id", PGUUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", PGUUID(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    list_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("lists.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[float] = mapped_column(Float, nullable=False, default=65535.0)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assignee_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    board_list: Mapped["BoardList"] = relationship("BoardList", back_populates="cards")
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assignee_id])
    labels: Mapped[list["Label"]] = relationship(
        "Label", secondary=card_labels, back_populates="cards"
    )


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#64748b")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    board: Mapped["Board"] = relationship("Board", back_populates="labels")
    cards: Mapped[list["Card"]] = relationship(
        "Card", secondary=card_labels, back_populates="labels"
    )
