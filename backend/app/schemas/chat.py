"""Pydantic schemas for chat-related endpoints (sessions, messages, SSE)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.models.lead import BudgetRange, LeadState, Urgency
from app.models.session import SessionStatus
from app.schemas.common import BaseSchema

# --- Sessions ---

class SessionCreateResponse(BaseSchema):
    session_id: UUID
    created_at: datetime
    status: SessionStatus


class SessionDetailResponse(BaseSchema):
    session_id: UUID
    status: SessionStatus
    message_count: int
    created_at: datetime
    last_activity_at: datetime
    messages: list[MessageOut]
    lead: LeadOut | None
    events: list[LeadEventOut]


# --- Messages ---

class MessageCreate(BaseSchema):
    content: str = Field(..., min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content cannot be empty after strip")
        return v


class MessageOut(BaseSchema):
    id: UUID
    role: Literal["user", "agent", "system_event"]
    content: str
    latency_ms: int | None = None
    created_at: datetime


# --- Lead ---

class LeadOut(BaseSchema):
    id: UUID
    name: str | None
    service_interest: str | None
    complaint: str | None
    budget_range: BudgetRange
    urgency: Urgency
    score: int
    state: LeadState
    score_breakdown: dict[str, int]
    scheduled_slot: str | None
    updated_at: datetime


class LeadFieldUpdate(BaseSchema):
    name: str | None = None
    service_interest: str | None = None
    complaint: str | None = None
    budget_range: BudgetRange | None = None
    urgency: Urgency | None = None
    scheduled_slot: str | None = None


class ScoreUpdate(BaseSchema):
    total: int
    breakdown: dict[str, int]


class StateUpdate(BaseSchema):
    from_state: LeadState = Field(alias="from")
    to: LeadState


# --- Lead events ---

class LeadEventOut(BaseSchema):
    id: UUID
    event_type: str
    payload: dict[str, Any]
    created_at: datetime


# --- SSE payload types ---

class TypingEvent(BaseSchema):
    active: bool


class TokenEvent(BaseSchema):
    delta: str


class LeadUpdateEvent(BaseSchema):
    fields: dict[str, Any]


class TimelineEvent(BaseSchema):
    type: str
    payload: dict[str, Any]


class QuickReplyOption(BaseSchema):
    id: str
    label: str


class QuickRepliesEvent(BaseSchema):
    options: list[QuickReplyOption]


class DoneEvent(BaseSchema):
    latency_ms: int
    message_id: UUID
    cost_usd: float | None = None


class SSEError(BaseSchema):
    code: str
    message: str


class SSEMessage(BaseSchema):
    event: str
    data: dict[str, Any]


# --- Admin schemas ---

class AdminLoginRequest(BaseSchema):
    username: str
    password: str


class AdminLoginResponse(BaseSchema):
    token: str
    expires_at: datetime


class AdminSessionSummary(BaseSchema):
    session_id: UUID
    created_at: datetime
    last_activity_at: datetime
    message_count: int
    status: SessionStatus
    lead_name: str | None
    lead_state: LeadState | None
    lead_score: int | None


class AdminSessionsList(BaseSchema):
    total: int
    items: list[AdminSessionSummary]


class AdminKanbanColumn(BaseSchema):
    novo: list[LeadOut]
    em_qualificacao: list[LeadOut]
    qualificado: list[LeadOut]
    agendamento_proposto: list[LeadOut]
    handoff: list[LeadOut]


class AdminCostsToday(BaseSchema):
    calls: int
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_usd: float
    cost_brl: float


class AdminCostsHistoryItem(BaseSchema):
    date: str
    calls: int
    cost_brl: float


class AdminCostsBudget(BaseSchema):
    daily_tokens: int
    used_today: int
    percent_used: float


class AdminCostsResponse(BaseSchema):
    today: AdminCostsToday
    history: list[AdminCostsHistoryItem]
    budget: AdminCostsBudget


class AdminAgentInfo(BaseSchema):
    provider: str
    model: str
    prompt_version: str
    prompt_sha256: str
    temperature: float
    embedding_provider: str
    embedding_model: str | None
