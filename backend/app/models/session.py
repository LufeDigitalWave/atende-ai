"""Session model — a single conversation between visitor and Sofia."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SessionStatus(str, enum.Enum):
    active = "active"
    capped = "capped"
    expired = "expired"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.active,
        nullable=False,
        index=True,
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
    lead = relationship(
        "Lead", back_populates="session", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Session id={self.id} status={self.status}>"
