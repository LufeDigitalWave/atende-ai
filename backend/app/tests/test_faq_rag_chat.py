"""Regression coverage for the FAQ/RAG context reaching the streaming reply."""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import routes_chat
from app.models import Lead, Message, MessageRole, Session, SessionStatus
from app.schemas.chat import MessageCreate
from app.services import llm, prompt_factory_v3, retriever
from app.services.prompt_factory_v3 import FALLBACK_PROFILE
from app.services.rate_limit import RateLimiter
from app.services.retriever import RetrievalResult


@pytest.mark.asyncio
async def test_faq_reply_includes_knowledge_retrieved_for_current_message(monkeypatch):
    """An undefined or wrong query must not silently drop the knowledge context."""
    session = Session(
        id=UUID("ef8148b2-168b-4a0b-9fd2-b55f49cb2198"),
        status=SessionStatus.active,
        agent_type="faq_rag",
        niche="demo-support",
        message_count=0,
    )
    query = "Qual é o prazo de atendimento?"
    fact = "O prazo de atendimento é de dois dias úteis."
    lead = Lead(session_id=session.id, score=0)
    db = MagicMock(spec=AsyncSession)
    db.scalar = AsyncMock(side_effect=[session, lead])
    db.scalars = AsyncMock(return_value=[
        Message(session_id=session.id, role=MessageRole.user, content=query),
    ])
    db.commit = AsyncMock()

    search = MagicMock()
    search.retrieve = AsyncMock(return_value=[
        RetrievalResult(chunk_text=fact, source_file="support.md", similarity=0.9),
    ])
    monkeypatch.setattr(retriever, "get_retriever", lambda: search)
    monkeypatch.setattr(prompt_factory_v3, "get_cached_profile", lambda _: FALLBACK_PROFILE)
    monkeypatch.setattr(routes_chat, "get_rate_limiter", lambda: RateLimiter())
    monkeypatch.setattr(routes_chat, "check_budget", AsyncMock(return_value=(True, 0, 10000)))
    monkeypatch.setattr(routes_chat, "log_usage", AsyncMock())
    monkeypatch.setattr(routes_chat, "check_budget_and_alert", AsyncMock())

    class ContextReplyProvider:
        async def chat_stream(self, system_prompt, messages, temperature):
            response = fact if fact in system_prompt else "Base indisponível."
            yield response, 10, 10, 0

    monkeypatch.setattr(llm, "get_llm_provider", lambda: ContextReplyProvider())

    response = await routes_chat.send_message(
        str(session.id), MessageCreate(content=query), db,
    )
    stream = "".join([part async for part in response.body_iterator])
    events = [
        (event.splitlines()[0], json.loads(event.splitlines()[1].removeprefix("data: ")))
        for event in stream.strip().split("\n\n")
    ]
    reply = "".join(data["delta"] for event, data in events if event == "event: token")

    assert reply == fact
    assert events[-1][0] == "event: done"
    assert all(event != "event: error" for event, _ in events)
    search.retrieve.assert_awaited_once_with(db, query, top_k=5, namespace="demo-support")
    saved_replies = [
        call.args[0].content for call in db.add.call_args_list
        if isinstance(call.args[0], Message) and call.args[0].role == MessageRole.agent
    ]
    assert saved_replies == [fact]
