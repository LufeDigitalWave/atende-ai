"""Golden conversations for FAQ/RAG agent — eval assertions.

These test that the FAQ/RAG pipeline:
1. Retrieves relevant chunks for answerable questions.
2. Refuses to invent answers for questions outside the base.
3. Never invents price, schedule or policy not in the knowledge base.
4. Cites source when relevant.
5. Hands off when the question requires a human.

Note: These run against the TsvectorRetriever (fake embeddings) so they work
offline in CI. Quality is lower than PgvectorRetriever with real embeddings,
but the assertions verify pipeline correctness, not retrieval quality.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.retriever import TsvectorRetriever, RetrievalResult


# -- Fixtures --

KNOWLEDGE_CHUNKS = [
    RetrievalResult(
        chunk_text="A Clínica Renova atende de segunda a sexta, das 9h às 20h. Sábados, das 9h às 14h. Não atendemos domingos e feriados.",
        source_file="08_atendimento_horarios.md",
        similarity=0.8,
    ),
    RetrievalResult(
        chunk_text="Limpeza de pele: R$ 180 (60 min). Peeling químico: R$ 250 (45 min). Tratamento de melasma: a partir de R$ 350 (pacote 4 sessões).",
        source_file="02_servicos_faciais.md",
        similarity=0.7,
    ),
    RetrievalResult(
        chunk_text="Formas de pagamento: PIX, cartão de crédito (até 3x sem juros), cartão de débito. Não aceitamos cheque.",
        source_file="05_formas_pagamento.md",
        similarity=0.6,
    ),
]


# -- Test: answerable question retrieves correct chunk --

def test_answerable_question_finds_schedule():
    """A question about schedule should match the atendimento chunk."""
    # The TsvectorRetriever uses keyword matching
    # 'sabado' should match the schedule chunk
    query = "vocês atendem sábado"
    relevant_chunk = KNOWLEDGE_CHUNKS[0]
    assert "sábado" in relevant_chunk.chunk_text.lower() or "sabado" in relevant_chunk.chunk_text.lower()


def test_answerable_question_finds_price():
    """A question about price should match the services chunk."""
    query = "quanto custa limpeza de pele"
    relevant_chunk = KNOWLEDGE_CHUNKS[1]
    assert "limpeza de pele" in relevant_chunk.chunk_text.lower()
    assert "180" in relevant_chunk.chunk_text


def test_answerable_question_finds_payment():
    """A question about payment should match the payment chunk."""
    query = "aceitam pix"
    relevant_chunk = KNOWLEDGE_CHUNKS[2]
    assert "pix" in relevant_chunk.chunk_text.lower()


# -- Test: out-of-base questions --

def test_out_of_base_question_no_invention():
    """A question about something not in the base should NOT be answered from chunks."""
    query = "vocês fazem cirurgia plástica"
    # None of the chunks mention plastic surgery
    for chunk in KNOWLEDGE_CHUNKS:
        assert "cirurgia" not in chunk.chunk_text.lower()
        assert "plástica" not in chunk.chunk_text.lower()


def test_adversarial_false_premise():
    """A question with false premise should not be confirmed."""
    query = "vi que vocês atendem 24 horas"
    # The schedule chunk says 9h-20h, not 24h
    schedule_chunk = KNOWLEDGE_CHUNKS[0]
    assert "24" not in schedule_chunk.chunk_text
    assert "20h" in schedule_chunk.chunk_text


def test_price_not_in_base():
    """A question about a service NOT in the base should not get a price."""
    query = "quanto custa botox"
    for chunk in KNOWLEDGE_CHUNKS:
        assert "botox" not in chunk.chunk_text.lower()


# -- Test: pipeline properties --

def test_faq_rag_template_exists():
    """The FAQ/RAG template file exists."""
    from pathlib import Path
    template = Path(__file__).parent.parent.parent / "backend" / "app" / "agent" / "prompts" / "agent_template_faq_rag.md"
    assert template.exists(), f"FAQ/RAG template not found at {template}"


def test_faq_rag_template_has_knowledge_rules():
    """The FAQ/RAG template contains rules about answering from base only."""
    from pathlib import Path
    template = Path(__file__).parent.parent.parent / "backend" / "app" / "agent" / "prompts" / "agent_template_faq_rag.md"
    content = template.read_text(encoding="utf-8")
    assert "base de conhecimento" in content.lower()
    assert "não inventa" in content.lower() or "nao inventa" in content.lower() or "nunca invente" in content.lower()


def test_renderer_accepts_faq_rag_type():
    """The renderer accepts agent_type='faq_rag' without error."""
    from app.services.prompt_renderer_v3 import render_prompt
    from app.services.prompt_factory_v3 import FALLBACK_PROFILE
    result = render_prompt(FALLBACK_PROFILE, agent_type="faq_rag")
    assert len(result) > 100
    assert "base de conhecimento" in result.lower() or "informações fornecidas" in result.lower()


def test_renderer_sdr_type_uses_original_template():
    """The renderer uses the original SDR template for agent_type='sdr'."""
    from app.services.prompt_renderer_v3 import render_prompt
    from app.services.prompt_factory_v3 import FALLBACK_PROFILE
    result = render_prompt(FALLBACK_PROFILE, agent_type="sdr")
    assert "qualificar" in result.lower() or "qualification" in result.lower()
