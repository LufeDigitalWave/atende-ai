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

    # Generate dynamic prompt for the niche (factory v2: data-not-prompt)
    from app.services.prompt_factory import generate_niche_prompt, sanitize_niche
    niche = sanitize_niche(niche)
    cached = await generate_niche_prompt(niche)

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

    profile = cached.profile
    logger.info(f"created session {session.id} niche={niche} agent={profile.agent_name}")

    return {
        "session_id": str(session.id),
        "created_at": session.created_at.isoformat(),
        "status": session.status.value,
        "niche": niche,
        "agent_name": profile.agent_name,
        "company_name": profile.company_name,
        "suggestions": profile.suggestions,
        "opening_message": profile.opening_message,
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
    from app.agent.extractor import extract_fields, apply_extraction
    from app.agent.scoring import compute_score
    from app.agent.states import auto_transition
    from app.models import Lead, LeadState, LeadEvent, LeadEventType
    from app.services.llm import get_llm_provider
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

        # Load dynamic prompt from session→niche mapping (factory v2)
        from app.services.prompt_factory import get_cached_prompt
        session_niche = _session_niches.get(str(session.id), "consultoria empresarial")
        cached = get_cached_prompt(session_niche)
        if cached:
            system_prompt = cached.system_prompt
        else:
            # Fallback: should not happen (cache miss means generate was called on session creation)
            # but keeping as safety net
            logger.warning(f"cache miss for niche {session_niche}, regenerating")
            from app.services.prompt_factory import generate_niche_prompt
            cached = await generate_niche_prompt(session_niche)
            system_prompt = cached.system_prompt

        # Inject brevity + engagement instruction (WhatsApp style)
        system_prompt += """\n\n## REGRA CRÍTICA DE FORMATO:
- Responda com no MÁXIMO 3 frases curtas (≤ 200 chars total). Estilo WhatsApp.
- NUNCA use listas numeradas, NUNCA use markdown/negrito.
- SEMPRE termine com uma pergunta que avança a qualificação (puxa pro próximo campo).
- Na primeira mensagem: cumprimente brevemente, diga quem é (nome + empresa) e pergunte o que o cliente procura.
- Exemplo bom: "Oi! Sou a Mel da PetVida 🐾 O que posso fazer pelo seu pet hoje?"
- Exemplo ruim: "Olá! Como posso ajudar você hoje?" (genérico demais, sem contexto)"""

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

        # Extract fields
        extraction = extract_fields(body.content, agent_response, lead)
        changed = apply_extraction(lead, extraction)

        if changed:
            fields = {k: v for k, v in extraction.to_dict().items() if v is not None}
            yield f"event: lead_update\ndata: {json.dumps({'fields': fields})}\n\n"

        # Score
        new_score, breakdown = compute_score(lead)
        if new_score != lead.score:
            lead.score = new_score
            lead.score_breakdown = breakdown
            yield f"event: score_update\ndata: {json.dumps({'total': new_score, 'breakdown': breakdown})}\n\n"

        # State transition
        old_state = lead.state
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
