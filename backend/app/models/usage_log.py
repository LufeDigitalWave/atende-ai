"""UsageLog model — accounting per LLM call (model, tokens, cached, cost)."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CallType(str, enum.Enum):
    chat = "chat"
    extraction = "extraction"
    embedding = "embedding"


class UsageLog(Base):
    __tablename__ = "usage_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    call_type: Mapped[CallType] = mapped_column(
        Enum(CallType, name="call_type"), nullable=False, index=True
    )
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    input_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    cached_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal("0"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<UsageLog call={self.call_type} model={self.model} "
            f"in={self.input_tokens} out={self.output_tokens} cached={self.cached_tokens}>"
        )
