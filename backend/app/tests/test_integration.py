"""Integration test — full agent turn with FakeLLMProvider."""
import pytest

from app.agent.extractor import extract_fields
from app.agent.scoring import compute_score
from app.agent.states import auto_transition
from app.models import BudgetRange, Lead, LeadState, Urgency
from app.services.llm import FakeLLMProvider


@pytest.mark.asyncio
async def test_fake_provider_greeting():
    """FakeLLMProvider responds to greeting."""
    provider = FakeLLMProvider()
    messages = [{"role": "user", "content": "Oi!"}]
    response = ""
    async for token, *_ in provider.chat_stream("", messages):
        response += token
    assert "Sofia" in response or "Bem-vindo" in response


@pytest.mark.asyncio
async def test_fake_provider_service_question():
    """FakeLLMProvider responds to service question."""
    provider = FakeLLMProvider()
    messages = [{"role": "user", "content": "Quanto custa melasma?"}]
    response = ""
    async for token, *_ in provider.chat_stream("", messages):
        response += token
    assert len(response) > 0


def test_full_qualification_flow():
    """Simulate a full lead qualification: extract → score → transition."""
    # Start with empty lead
    lead = Lead(
        session_id="test",
        state=LeadState.novo,
        score=0,
        budget_range=BudgetRange.nao_informado,
        urgency=Urgency.nao_informada,
    )
    assert lead.score == 0
    assert lead.state == LeadState.novo

    # Turn 1: Greeting + name
    msg1 = "Oi, meu nome é João"
    ext1 = extract_fields(msg1, "", lead)
    assert ext1.name == "João"
    lead.name = ext1.name
    trans1 = auto_transition(lead)
    assert trans1 is not None
    assert trans1.to_state == LeadState.em_qualificacao
    lead.state = LeadState.em_qualificacao
    score1, _ = compute_score(lead)
    assert score1 == 20  # name only

    # Turn 2: Service + complaint + budget
    msg2 = "Quero tratar melasma, tenho manchas no rosto, posso gastar 3 mil"
    ext2 = extract_fields(msg2, "", lead)
    assert ext2.service_interest == "melasma"
    assert ext2.complaint == "manchas"
    assert ext2.budget_range == BudgetRange.ate_3k
    lead.service_interest = ext2.service_interest
    lead.complaint = ext2.complaint
    lead.budget_range = ext2.budget_range
    score2, breakdown2 = compute_score(lead)
    lead.score = score2
    # name(20) + service(20) + complaint(15) + budget(20) + bonus(10) = 85
    assert score2 > score1
    assert "budget_mid_or_high" in breakdown2

    # Turn 3: Urgency
    msg3 = "Preciso começar logo"
    ext3 = extract_fields(msg3, "", lead)
    assert ext3.urgency == Urgency.alta
    lead.urgency = ext3.urgency
    score3, breakdown3 = compute_score(lead)
    lead.score = score3
    assert score3 == 100  # capped (all 5 fields + bonuses)
    trans3 = auto_transition(lead)
    assert trans3 is not None
    assert trans3.to_state == LeadState.qualificado
    assert "urgency_alta" in breakdown3

    # Verify full state
    assert lead.name == "João"
    assert lead.service_interest == "melasma"
    assert lead.complaint == "manchas"
    assert lead.budget_range == BudgetRange.ate_3k
    assert lead.urgency == Urgency.alta
    assert lead.score == 100
