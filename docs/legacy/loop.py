"""Agent loop — orchestrates one turn of conversation.

Flow: retrieve (RAG) → chat (LLM) → extract (fields) → score → state transition → events
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.extractor import apply_extraction, extract_fields
from app.agent.scoring import compute_score
from app.agent.states import auto_transition, can_transition
from app.core.config import get_settings
from app.models import LeadEvent, LeadEventType, Message, MessageRole, Session
from app.services.llm import get_llm_provider
from app.services.retriever import get_retriever

logger = structlog.get_logger("agent_loop")


class AgentTurn:
    """Result of one agent turn."""

    def __init__(
        self,
        agent_response: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cached_tokens: int = 0,
        events: list[dict[str, Any]] | None = None,
    ):
        self.agent_response = agent_response
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.cached_tokens = cached_tokens
        self.events = events or []


def _load_prompt(version: str) -> str:
    """Load prompt from file."""
    prompt_dir = Path(__file__).parent / "prompts"
    prompt_file = prompt_dir / f"{version}.md"
    if not prompt_file.exists():
        raise RuntimeError(f"prompt not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


async def run_agent_turn(
    session_db: Session,
    lead_db: Any,  # Lead model (avoid circular import)
    user_message: str,
    db_session: AsyncSession,
) -> AgentTurn:
    """
    Run one turn of the agent.

    Steps:
    1. Retrieve (RAG top-3 if heuristic says query)
    2. Build prompt (system + lead_profile + history + RAG)
    3. Chat stream (LLM)
    4. Extract (parallel extractor)
    5. Score (deterministic)
    6. State transition (FSM)
    7. Generate events
    """
    settings = get_settings()
    events = []

    # 1. Retrieve (simple heuristic: if msg has "?", likely a question)
    retrieved_chunks = []
    if "?" in user_message or len(user_message.split()) < 20:
        retriever = get_retriever()
        try:
            retrieved_chunks = await retriever.retrieve(db_session, user_message, top_k=3)
            logger.info(f"retrieved {len(retrieved_chunks)} chunks")
        except Exception as e:
            logger.warning(f"retrieval failed: {e}")

    # 2. Build prompt
    prompt_text = _load_prompt(settings.agent_prompt_version)
    rag_context = "\n\n".join(
        [f"**{c.source_file}:**\n{c.chunk_text}" for c in retrieved_chunks]
    )
    rag_section = f"\n\n## Base de Conhecimento:\n{rag_context}" if rag_context else ""

    # Build message history (last 12 messages or 6 turns)
    history_messages = []
    messages = await db_session.query(Message).filter(
        Message.session_id == session_db.id
    ).order_by(Message.created_at.desc()).limit(12).all()
    for msg in reversed(messages):
        history_messages.append({"role": msg.role.value, "content": msg.content})

    # Lead profile summary
    lead_profile_text = f"""
## Lead Profile:
- Name: {lead_db.name or "not set"}
- Service Interest: {lead_db.service_interest or "not set"}
- Complaint: {lead_db.complaint or "not set"}
- Budget Range: {lead_db.budget_range.value}
- Urgency: {lead_db.urgency.value}
- Current Score: {lead_db.score}
- State: {lead_db.state.value}
"""

    # Build full system prompt
    system_prompt = f"{prompt_text}{rag_section}{lead_profile_text}"

    # 3. Stream chat
    llm_provider = get_llm_provider()
    agent_response = ""
    async for token in llm_provider.chat_stream(
        system_prompt, history_messages, settings.agent_temperature
    ):
        agent_response += token
        yield {"event": "token", "data": {"delta": token}}

    # Save agent message
    agent_msg = Message(
        session_id=session_db.id,
        role=MessageRole.agent,
        content=agent_response,
    )
    db_session.add(agent_msg)
    await db_session.flush()

    # 4. Extract in parallel
    extraction = extract_fields(user_message, agent_response, lead_db)
    extraction_changed = apply_extraction(lead_db, extraction)

    if extraction_changed:
        fields = {k: v for k, v in extraction.to_dict().items() if v is not None}
        yield {"event": "lead_update", "data": {"fields": fields}}
        events.append(
            {
                "type": LeadEventType.field_extracted,
                "payload": {"extracted_fields": fields},
            }
        )

    # 5. Score (deterministic)
    new_score, breakdown = compute_score(lead_db)
    if new_score != lead_db.score:
        lead_db.score = new_score
        lead_db.score_breakdown = breakdown
        yield {
            "event": "score_update",
            "data": {"total": new_score, "breakdown": breakdown},
        }
        events.append(
            {
                "type": LeadEventType.score_updated,
                "payload": {"score": new_score, "breakdown": breakdown},
            }
        )

    # 6. State transition (auto + explicit)
    old_state = lead_db.state
    trans = auto_transition(lead_db)
    if trans and trans.allowed:
        lead_db.state = trans.to_state
        yield {
            "event": "state_update",
            "data": {"from": old_state.value, "to": trans.to_state.value},
        }
        events.append(
            {
                "type": LeadEventType.state_changed,
                "payload": {"from": old_state.value, "to": trans.to_state.value},
            }
        )

    # 7. Save all
    session_db.message_count += 1
    await db_session.commit()

    # Create lead events
    for evt in events:
        lead_event = LeadEvent(
            lead_id=lead_db.id,
            event_type=evt["type"],
            payload=evt["payload"],
        )
        db_session.add(lead_event)
    await db_session.commit()

    # Return final result
    yield {
        "event": "done",
        "data": {
            "latency_ms": 0,  # TODO: measure
            "message_id": str(agent_msg.id),
            "cost_usd": None,  # TODO: compute from usage_log
        },
    }
