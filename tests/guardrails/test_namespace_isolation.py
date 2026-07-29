"""Guardrail: tenant isolation — namespace A must NOT read data from namespace B.

This test verifies that the retriever filters by namespace correctly.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.retriever import TsvectorRetriever, RetrievalResult


@pytest.fixture
def retriever():
    return TsvectorRetriever()


@pytest.mark.asyncio
async def test_tsvector_query_includes_namespace_filter():
    """TsvectorRetriever SQL must include namespace = :ns in WHERE clause."""
    retriever = TsvectorRetriever()

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(__iter__=lambda s: iter([])))

    await retriever.retrieve(mock_session, "test query", top_k=3, namespace="tenant_a")

    # Verify the execute was called
    assert mock_session.execute.called
    call_args = mock_session.execute.call_args

    # The second argument should be the params dict
    params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
    assert params.get("ns") == "tenant_a", f"Expected namespace 'tenant_a' in params, got: {params}"


@pytest.mark.asyncio
async def test_different_namespaces_get_different_params():
    """Two calls with different namespaces must pass different :ns values."""
    retriever = TsvectorRetriever()

    calls = []

    async def capture_execute(stmt, params):
        calls.append(params.copy())
        return MagicMock(__iter__=lambda s: iter([]))

    mock_session = AsyncMock()
    mock_session.execute = capture_execute

    await retriever.retrieve(mock_session, "price", top_k=3, namespace="client_a")
    await retriever.retrieve(mock_session, "price", top_k=3, namespace="client_b")

    assert len(calls) == 2
    assert calls[0]["ns"] == "client_a"
    assert calls[1]["ns"] == "client_b"


def test_knowledge_chunk_model_has_namespace():
    """KnowledgeChunk model has a namespace column."""
    from app.models.knowledge import KnowledgeChunk
    columns = {c.name for c in KnowledgeChunk.__table__.columns}
    assert "namespace" in columns


def test_knowledge_chunk_namespace_default():
    """KnowledgeChunk.namespace defaults to 'default'."""
    from app.models.knowledge import KnowledgeChunk
    col = KnowledgeChunk.__table__.columns["namespace"]
    assert col.default.arg == "default"
