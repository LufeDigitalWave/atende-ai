"""FunnelEvent model — server-side conversion funnel tracking.

Events tracked (no PII stored):
- view_landing
- start_demo
- first_message
- reached_qualified
- lead_captured
- clicked_pricing
- clicked_whatsapp
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FunnelStep(str, enum.Enum):
    view_landing = "view_landing"
    start_demo = "start_demo"
    first_message = "first_message"
    reached_qualified = "reached_qualified"
    lead_captured = "lead_captured"
    clicked_pricing = "clicked_pricing"
    clicked_whatsapp = "clicked_whatsapp"


class FunnelEvent(Base):
    __tablename__ = "funnel_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    step: Mapped[FunnelStep] = mapped_column(
        Enum(FunnelStep, name="funnel_step"), nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    ip_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<FunnelEvent step={self.step}>"
