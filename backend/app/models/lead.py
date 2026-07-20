"""Lead model — the qualified profile extracted from a session."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LeadState(str, enum.Enum):
    novo = "novo"
    em_qualificacao = "em_qualificacao"
    qualificado = "qualificado"
    agendamento_proposto = "agendamento_proposto"
    handoff = "handoff"


class BudgetRange(str, enum.Enum):
    nao_informado = "nao_informado"
    ate_1k = "ate_1k"
    ate_3k = "ate_3k"
    ate_6k = "ate_6k"
    acima_6k = "acima_6k"


class Urgency(str, enum.Enum):
    nao_informada = "nao_informada"
    baixa = "baixa"
    media = "media"
    alta = "alta"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 5 qualification fields
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    service_interest: Mapped[str | None] = mapped_column(String(120), nullable=True)
    complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_range: Mapped[BudgetRange] = mapped_column(
        Enum(BudgetRange, name="budget_range"),
        default=BudgetRange.nao_informado,
        nullable=False,
    )
    urgency: Mapped[Urgency] = mapped_column(
        Enum(Urgency, name="urgency"),
        default=Urgency.nao_informada,
        nullable=False,
    )

    # Audit
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[LeadState] = mapped_column(
        Enum(LeadState, name="lead_state"),
        default=LeadState.novo,
        nullable=False,
        index=True,
    )
    score_breakdown: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # Agendamento fictício (slot escolhido pelo visitante)
    scheduled_slot: Mapped[str | None] = mapped_column(String(120), nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    session = relationship("Session", back_populates="lead")
    events = relationship(
        "LeadEvent", back_populates="lead", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Lead name={self.name!r} score={self.score} state={self.state}>"