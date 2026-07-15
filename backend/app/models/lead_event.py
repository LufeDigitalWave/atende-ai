"""LeadEvent model — append-only timeline of events for a lead."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LeadEventType(str, enum.Enum):
    session_started = "session_started"
    field_extracted = "field_extracted"
    score_updated = "score_updated"
    state_changed = "state_changed"
    handoff_triggered = "handoff_triggered"
    slot_offered = "slot_offered"
    slot_picked = "slot_picked"
    human_requested = "human_requested"
    out_of_scope = "out_of_scope"
    session_capped = "session_capped"


class LeadEvent(Base):
    __tablename__ = "lead_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[LeadEventType] = mapped_column(
        Enum(LeadEventType, name="lead_event_type"), nullable=False, index=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    lead = relationship("Lead", back_populates="events")

    def __repr__(self) -> str:
        return f"<LeadEvent type={self.event_type}>"