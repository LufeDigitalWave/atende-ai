"""Test field extraction from messages."""
import pytest

from app.agent.extractor import extract_fields
from app.models import BudgetRange, Lead, LeadState, Urgency


@pytest.fixture
def empty_lead() -> Lead:
    return Lead(
        session_id="dummy",
        state=LeadState.novo,
        budget_range=BudgetRange.nao_informado,
        urgency=Urgency.nao_informada,
    )


def test_extract_name_variants(empty_lead):
    """Extract name from common patterns."""
    variants = [
        ("meu nome é João", "João"),
        ("eu sou Maria", "Maria"),
        ("chamo Pedro", "Pedro"),
    ]
    for msg, expected_name in variants:
        result = extract_fields(msg, "", empty_lead)
        assert result.name == expected_name, f"failed for {msg}"


def test_extract_service(empty_lead):
    """Extract service from keywords."""
    variants = [
        "quero tratar melasma",
        "tenho acne",
        "quero depilação a laser",
        "limpeza de pele",
    ]
    for msg in variants:
        result = extract_fields(msg, "", empty_lead)
        assert result.service_interest is not None


def test_extract_budget_range(empty_lead):
    """Extract budget range from keywords."""
    variants = [
        ("posso gastar até 1 mil", BudgetRange.ate_1k),
        ("meu orçamento é 3 mil", BudgetRange.ate_3k),
        ("tenho até 6 mil", BudgetRange.ate_6k),
    ]
    for msg, expected_range in variants:
        result = extract_fields(msg, "", empty_lead)
        assert result.budget_range == expected_range, f"failed for {msg}"


def test_extract_urgency_alta(empty_lead):
    """Extract high urgency."""
    variants = ["urgente", "quero logo", "amanhã mesmo", "preciso já"]
    for msg in variants:
        result = extract_fields(msg, "", empty_lead)
        assert result.urgency == Urgency.alta, f"failed for {msg}"


def test_extract_urgency_baixa(empty_lead):
    """Extract low urgency."""
    variants = ["sem pressa", "quando possível", "aos poucos"]
    for msg in variants:
        result = extract_fields(msg, "", empty_lead)
        assert result.urgency == Urgency.baixa, f"failed for {msg}"


def test_extract_multi_field_single_message(empty_lead):
    """Extract multiple fields from one message."""
    msg = "Oi, meu nome é João, quero tratar melasma, posso gastar 3 mil"
    result = extract_fields(msg, "", empty_lead)
    assert result.name == "João"
    assert result.service_interest == "melasma"
    assert result.budget_range == BudgetRange.ate_3k


def test_extract_complaint(empty_lead):
    """Extract complaint/problem description."""
    variants = ["tenho cicatrizes", "acne no rosto", "queda de cabelo"]
    for msg in variants:
        result = extract_fields(msg, "", empty_lead)
        assert result.complaint is not None, f"failed for {msg}"
