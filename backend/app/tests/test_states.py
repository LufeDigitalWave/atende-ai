"""Test FSM state transitions."""
import pytest

from app.agent.states import auto_transition, can_transition
from app.models import BudgetRange, Lead, LeadState, Urgency


def test_novo_to_qualificacao_allowed():
    """novo → em_qualificacao always allowed."""
    trans = can_transition(LeadState.novo, LeadState.em_qualificacao)
    assert trans.allowed


def test_qualificacao_to_qualificado_allowed():
    """em_qualificacao → qualificado allowed."""
    trans = can_transition(LeadState.em_qualificacao, LeadState.qualificado)
    assert trans.allowed


def test_backward_transition_forbidden():
    """qualificado → em_qualificacao forbidden (backward)."""
    trans = can_transition(LeadState.qualificado, LeadState.em_qualificacao)
    assert not trans.allowed
    assert "backward" in trans.reason.lower()


def test_any_to_handoff_allowed():
    """Any state → handoff allowed (escape hatch)."""
    for state in [LeadState.novo, LeadState.em_qualificacao, LeadState.qualificado]:
        trans = can_transition(state, LeadState.handoff)
        assert trans.allowed


def test_auto_transition_novo_with_any_field():
    """novo + any field → auto-promote to em_qualificacao."""
    lead = Lead(
        session_id="dummy",
        state=LeadState.novo,
        budget_range=BudgetRange.nao_informado,
        urgency=Urgency.nao_informada,
    )
    lead.name = "João"
    trans = auto_transition(lead)
    assert trans is not None
    assert trans.to_state == LeadState.em_qualificacao


def test_auto_transition_qualificacao_with_all_fields():
    """em_qualificacao + all 5 fields → auto-promote to qualificado."""
    lead = Lead(
        session_id="dummy",
        state=LeadState.em_qualificacao,
        name="João",
        service_interest="melasma",
        complaint="manchas",
        budget_range=BudgetRange.ate_3k,
        urgency=Urgency.alta,
    )
    trans = auto_transition(lead)
    assert trans is not None
    assert trans.to_state == LeadState.qualificado


def test_auto_transition_no_promotion_if_incomplete():
    """em_qualificacao + 4 fields → no auto-transition."""
    lead = Lead(
        session_id="dummy",
        state=LeadState.em_qualificacao,
        name="João",
        service_interest="melasma",
        complaint="manchas",
        budget_range=BudgetRange.ate_3k,
        # urgency missing
        urgency=Urgency.nao_informada,
    )
    trans = auto_transition(lead)
    assert trans is None  # no transition
