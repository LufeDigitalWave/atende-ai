"""Chat routes — sessions, messages, SSE events.

Endpoints:
- POST /api/sessions — create session
- GET /api/sessions/{id} — get session state
- POST /api/sessions/{id}/messages — send message (SSE stream)
- GET /api/sessions/{id}/events — connect SSE only
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.ip_hash import get_client_ip, hash_ip
from app.core.config import get_settings
from app.models import Lead, Session, SessionStatus, Message, MessageRole
from app.schemas.chat import (
    MessageCreate,
    SessionDetailResponse,
    MessageOut,
    LeadOut,
)
from app.schemas.common import BaseSchema
from app.services.budget import check_budget
from app.services.rate_limit import get_rate_limiter

logger = structlog.get_logger("routes_chat")
router = APIRouter(prefix="/api", tags=["chat"])
settings = get_settings()

# In-memory session→niche mapping (populated on session creation)
_session_niches: dict[str, str] = {}


def _build_lead_summary(lead) -> str:
    """Build a short text summary of the lead's current state for the extractor."""
    parts = []
    if lead.name:
        parts.append(f"nome={lead.name}")
    if lead.service_interest:
        parts.append(f"servico={lead.service_interest}")
    if lead.complaint:
        parts.append(f"queixa={lead.complaint}")
    if lead.budget_range and lead.budget_range.value != "nao_informado":
        parts.append(f"orcamento={lead.budget_range.value}")
    if lead.urgency and lead.urgency.value != "nao_informada":
        parts.append(f"urgencia={lead.urgency.value}")
    return ", ".join(parts) if parts else "(lead vazio)"


class SessionCreateRequest(BaseSchema):
    niche: str = ""


@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: Request,
    body: SessionCreateRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new session with optional niche.

    If niche provided, generates a dynamic prompt for that industry.
    Returns session info + agent metadata (name, company, suggestions).
    """
    # Get client IP
    ip = get_client_ip(request)
    ip_hash = hash_ip(ip)

    # Check rate limit
    limiter = get_rate_limiter()
    allowed, reason = limiter.record_new_session(ip_hash)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
        )

    # Parse niche
    niche = (body.niche if body else "") or "clinica de estetica"

    # Generate dynamic prompt for the niche (factory v3: BusinessProfile + ConversationProfile)
    from app.services.prompt_factory_v3 import generate_niche_profile, sanitize_niche
    niche = sanitize_niche(niche)
    niche_profile = await generate_niche_profile(niche)

    # Create session
    session = Session(
        ip_hash=ip_hash,
        status=SessionStatus.active,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Create lead profile
    lead = Lead(
        session_id=session.id,
    )
    db.add(lead)
    await db.commit()

    # Store niche for this session (in-memory lookup for SSE generator)
    _session_niches[str(session.id)] = niche

    bp = niche_profile.business
    logger.info(f"created session {session.id} niche={niche} agent={bp.agent_name}")

    return {
        "session_id": str(session.id),
        "created_at": session.created_at.isoformat(),
        "status": session.status.value,
        "niche": niche,
        "agent_name": bp.agent_name,
        "company_name": bp.company_name,
        "suggestions": bp.suggestions,
        "opening_message": bp.opening_message,
    }


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    """
    Get session state (messages + lead + events).
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid session_id format",
        )

    # Query with eager loading
    stmt = (
        select(Session)
        .where(Session.id == sid)
        .options(
            selectinload(Session.messages),
            selectinload(Session.lead).selectinload(Lead.events),
        )
    )
    session = await db.scalar(stmt)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found",
        )

    # Build response
    messages = [
        MessageOut(
            id=m.id,
            role=m.role.value,
            content=m.content,
            latency_ms=m.latency_ms,
            created_at=m.created_at,
        )
        for m in (session.messages or [])
    ]

    lead_out = None
    if session.lead:
        lead_out = LeadOut(
            id=session.lead.id,
            name=session.lead.name,
            service_interest=session.lead.service_interest,
            complaint=session.lead.complaint,
            budget_range=session.lead.budget_range,
            urgency=session.lead.urgency,
            score=session.lead.score,
            state=session.lead.state,
            score_breakdown=session.lead.score_breakdown,
            scheduled_slot=session.lead.scheduled_slot,
            updated_at=session.lead.updated_at,
        )

    return SessionDetailResponse(
        session_id=session.id,
        status=session.status,
        message_count=session.message_count,
        created_at=session.created_at,
        last_activity_at=session.last_activity_at,
        messages=messages,
        lead=lead_out,
        events=[],  # TODO: implement from lead.events
    )


@router.post(
    "/sessions/{session_id}/messages",
    status_code=status.HTTP_200_OK,
)
async def send_message(
    session_id: str,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Send message — SSE stream with agent response + CRM updates + events.

    Checks:
    - Session exists and is active
    - Rate limit (1 msg/2s)
    - Budget available
    - Message count cap (30)
    - Input length (500 chars)
    """
    # Parse session ID
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid session_id format",
        )

    # Fetch session
    session = await db.scalar(select(Session).where(Session.id == sid))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found",
        )

    # Check status
    if session.status == SessionStatus.capped:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="session capped (max messages reached)",
        )
    if session.status == SessionStatus.expired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="session expired",
        )

    # Check input length
    if len(body.content) > settings.max_input_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"message too long (max {settings.max_input_chars} chars)",
        )

    # Rate limit
    limiter = get_rate_limiter()
    allowed, reason = limiter.check_session_rate_limit(session.id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
        )

    # Budget check
    budget_ok, used, remaining = await check_budget(db, projected_tokens=500)
    if not budget_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="demo in high demand — please try again later",
            headers={"X-Budget-Status": "exceeded"},
        )

    # Cap check
    if session.message_count >= settings.max_messages_per_session:
        session.status = SessionStatus.capped
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="session reached max messages",
        )

    # Save user message
    user_msg = Message(
        session_id=session.id,
        role=MessageRole.user,
        content=body.content,
    )
    db.add(user_msg)
    session.message_count += 1
    session.last_activity_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"message sent to session {session.id}")

    # Run agent loop and stream response as SSE
    from fastapi.responses import StreamingResponse
    from app.agent.states import auto_transition
    from app.models import Lead, LeadState, LeadEvent, LeadEventType, BudgetRange, Urgency
    from app.services.llm import get_llm_provider
    from app.services.lead_extractor import extract_lead_data
    from app.services.lead_scoring_v3 import compute_score_v3
    from app.services.prompt_factory_v3 import get_cached_profile, generate_niche_profile
    from app.services.prompt_renderer_v3 import render_prompt
    from pathlib import Path
    import json
    import time

    async def generate_sse():
        """SSE generator — runs agent loop and yields events."""
        start_time = time.time()

        # Load lead
        lead = await db.scalar(select(Lead).where(Lead.session_id == session.id))
        if not lead:
            yield f"event: error\ndata: {json.dumps({'code': 'no_lead', 'message': 'Lead not found'})}\n\n"
            return

        # Load dynamic prompt from session→niche mapping (factory v3)
        session_niche = _session_niches.get(str(session.id), "consultoria empresarial")
        niche_profile = get_cached_profile(session_niche)
        if not niche_profile:
            logger.warning(f"v3 cache miss for niche {session_niche}, regenerating")
            niche_profile = await generate_niche_profile(session_niche)

        # Render system prompt from NicheProfile (template v3)
        system_prompt = render_prompt(niche_profile)

        # Build history (last 12 messages)
        history_stmt = (
            select(Message)
            .where(Message.session_id == session.id)
            .order_by(Message.created_at.desc())
            .limit(12)
        )
        history_result = await db.scalars(history_stmt)
        history_msgs = list(reversed(list(history_result)))
        messages_for_llm = [
            {"role": m.role.value if m.role.value != "agent" else "assistant", "content": m.content}
            for m in history_msgs
        ]

        # Typing indicator
        yield f"event: typing\ndata: {json.dumps({'active': True})}\n\n"

        # Stream LLM response
        llm = get_llm_provider()
        agent_response = ""
        try:
            async for token, inp_tok, out_tok, cached_tok in llm.chat_stream(
                system_prompt, messages_for_llm, settings.agent_temperature
            ):
                agent_response += token
                yield f"event: token\ndata: {json.dumps({'delta': token})}\n\n"
        except Exception as e:
            logger.error(f"LLM error: {e}")
            yield f"event: error\ndata: {json.dumps({'code': 'llm_error', 'message': str(e)})}\n\n"
            return

        # Save agent message
        agent_msg = Message(
            session_id=session.id,
            role=MessageRole.agent,
            content=agent_response,
            latency_ms=int((time.time() - start_time) * 1000),
        )
        db.add(agent_msg)
        await db.commit()

        # Extract fields via LLM (v3 — dynamic per niche)
        existing_summary = _build_lead_summary(lead)
        extraction = await extract_lead_data(
            body.content, agent_response, niche_profile, existing_summary
        )

        # Apply extraction to legacy lead columns (backward compat with frontend SSE)
        legacy_fields = extraction.to_legacy_dict()
        changed = False
        if legacy_fields.get("name") and not lead.name:
            lead.name = legacy_fields["name"]
            changed = True
        if legacy_fields.get("service_interest") and not lead.service_interest:
            lead.service_interest = legacy_fields["service_interest"]
            changed = True
        if legacy_fields.get("complaint") and not lead.complaint:
            lead.complaint = legacy_fields["complaint"]
            changed = True

        # Also emit ALL extracted fields (not just legacy ones)
        all_fields = {ef.key: ef.value for ef in extraction.extracted_fields if ef.value is not None}
        if legacy_fields:
            all_fields.update(legacy_fields)
        if all_fields:
            changed = True
            yield f"event: lead_update\ndata: {json.dumps({'fields': all_fields})}\n\n"

        # Score (v3 — contextual by intent)
        new_score, breakdown = compute_score_v3(extraction, niche_profile)
        if new_score != lead.score:
            lead.score = new_score
            lead.score_breakdown = breakdown
            yield f"event: score_update\ndata: {json.dumps({'total': new_score, 'breakdown': breakdown})}\n\n"

        # State transition (keep legacy FSM for now, enhanced with handoff detection)
        old_state = lead.state
        if extraction.should_handoff:
            lead.state = LeadState.handoff
            yield f"event: state_update\ndata: {json.dumps({'from': old_state.value, 'to': 'handoff'})}\n\n"
        else:
            trans = auto_transition(lead)
            if trans and trans.allowed:
                lead.state = trans.to_state
                yield f"event: state_update\ndata: {json.dumps({'from': old_state.value, 'to': trans.to_state.value})}\n\n"

        await db.commit()

        # Done
        latency_ms = int((time.time() - start_time) * 1000)
        yield f"event: done\ndata: {json.dumps({'latency_ms': latency_ms, 'message_id': str(agent_msg.id)})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions/{session_id}/events",
    response_model=None,
)
async def stream_events(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Connect to SSE stream for lead updates and agent events.

    TODO: implement SSE generator in passo 5.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid session_id format",
        )

    # Verify session exists
    session = await db.scalar(select(Session).where(Session.id == sid))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found",
        )

    logger.info(f"SSE connected to session {session.id}")

    # TODO: Stream events via async generator
    return {"status": "sse_connected"}
