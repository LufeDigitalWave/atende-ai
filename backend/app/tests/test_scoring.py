"""Test lead scoring — deterministic and explainable."""
import pytest

from app.agent.scoring import compute_score
from app.models import BudgetRange, Lead, LeadState, Urgency


@pytest.fixture
def empty_lead() -> Lead:
    """Fresh lead with no fields."""
    return Lead(
        session_id="dummy",
        state=LeadState.novo,
        budget_range=BudgetRange.nao_informado,
        urgency=Urgency.nao_informada,
    )


def test_score_empty_lead(empty_lead):
    """Empty lead scores 0."""
    score, breakdown = compute_score(empty_lead)
    assert score == 0
    assert breakdown["total"] == 0


def test_score_name_filled(empty_lead):
    """Name filled +20."""
    empty_lead.name = "João"
    score, breakdown = compute_score(empty_lead)
    assert score == 20
    assert breakdown["name_filled"] == 20


def test_score_service_filled(empty_lead):
    """Service +20."""
    empty_lead.service_interest = "melasma"
    score, breakdown = compute_score(empty_lead)
    assert score == 20
    assert breakdown["service_interest_filled"] == 20


def test_score_complaint_filled(empty_lead):
    """Complaint +15."""
    empty_lead.complaint = "manchas no rosto"
    score, breakdown = compute_score(empty_lead)
    assert score == 15
    assert breakdown["complaint_filled"] == 15


def test_score_budget_low(empty_lead):
    """Budget ate_1k +20, no bonus."""
    empty_lead.budget_range = BudgetRange.ate_1k
    score, breakdown = compute_score(empty_lead)
    assert score == 20
    assert breakdown["budget_range_set"] == 20
    assert "budget_mid_or_high" not in breakdown


def test_score_budget_mid_bonus(empty_lead):
    """Budget ate_3k +20 +10 bonus."""
    empty_lead.budget_range = BudgetRange.ate_3k
    score, breakdown = compute_score(empty_lead)
    assert score == 30
    assert breakdown["budget_range_set"] == 20
    assert breakdown["budget_mid_or_high"] == 10


def test_score_urgency_low(empty_lead):
    """Urgency baixa +15, no bonus."""
    empty_lead.urgency = Urgency.baixa
    score, breakdown = compute_score(empty_lead)
    assert score == 15
    assert breakdown["urgency_set"] == 15
    assert "urgency_alta" not in breakdown


def test_score_urgency_alta_bonus(empty_lead):
    """Urgency alta +15 +10 bonus."""
    empty_lead.urgency = Urgency.alta
    score, breakdown = compute_score(empty_lead)
    assert score == 25
    assert breakdown["urgency_set"] == 15
    assert breakdown["urgency_alta"] == 10


def test_score_all_fields_complete(empty_lead):
    """All 5 fields: 20+20+15+20+10+15+10 = 110 → capped at 100."""
    empty_lead.name = "João"
    empty_lead.service_interest = "melasma"
    empty_lead.complaint = "manchas"
    empty_lead.budget_range = BudgetRange.ate_3k
    empty_lead.urgency = Urgency.alta
    score, breakdown = compute_score(empty_lead)
    assert score == 100  # capped
    assert breakdown["total"] == 110  # actual sum


def test_score_breakdown_integrity(empty_lead):
    """Score breakdown sums to total."""
    empty_lead.name = "João"
    empty_lead.service_interest = "melasma"
    empty_lead.budget_range = BudgetRange.ate_3k
    score, breakdown = compute_score(empty_lead)
    components_sum = sum(v for k, v in breakdown.items() if k != "total")
    assert breakdown["total"] == components_sum
