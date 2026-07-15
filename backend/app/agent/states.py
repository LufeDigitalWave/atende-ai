"""FSM for lead state transitions."""
from __future__ import annotations

from app.models import Lead, LeadState


class StateTransition:
    """Result of a state transition attempt."""

    def __init__(
        self,
        from_state: LeadState,
        to_state: LeadState,
        allowed: bool,
        reason: str = "",
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.allowed = allowed
        self.reason = reason

    def __repr__(self) -> str:
        status = "✓" if self.allowed else "✗"
        return f"<Transition {status} {self.from_state} -> {self.to_state}>"


def can_transition(
    from_state: LeadState, to_state: LeadState
) -> StateTransition:
    """
    Check if transition is allowed.

    **FSM rules:**
    - novo → em_qualificacao (always)
    - em_qualificacao → qualificado (when 5 fields complete)
    - em_qualificacao → handoff (when explicit request)
    - qualificado → agendamento_proposto (when slots offered)
    - agendamento_proposto → handoff (when slot picked)
    - * → handoff (always allowed, "escape hatch")
    - All backward transitions forbidden
    """

    # Always allow forward to handoff
    if to_state == LeadState.handoff:
        return StateTransition(from_state, to_state, True)

    # Backward transitions forbidden
    order = [
        LeadState.novo,
        LeadState.em_qualificacao,
        LeadState.qualificado,
        LeadState.agendamento_proposto,
        LeadState.handoff,
    ]
    if order.index(to_state) < order.index(from_state):
        return StateTransition(
            from_state, to_state, False, "backward transitions not allowed"
        )

    # Forward transitions
    if from_state == LeadState.novo and to_state == LeadState.em_qualificacao:
        return StateTransition(from_state, to_state, True)
    if from_state == LeadState.em_qualificacao and to_state == LeadState.qualificado:
        return StateTransition(from_state, to_state, True)
    if (
        from_state == LeadState.qualificado
        and to_state == LeadState.agendamento_proposto
    ):
        return StateTransition(from_state, to_state, True)
    if (
        from_state == LeadState.agendamento_proposto
        and to_state == LeadState.handoff
    ):
        return StateTransition(from_state, to_state, True)

    # Otherwise forbidden
    return StateTransition(
        from_state, to_state, False, "transition not in FSM"
    )


def auto_transition(lead: Lead) -> StateTransition | None:
    """
    Automatically transition based on qualification progress.

    Rules:
    - If in novo and has any field, move to em_qualificacao
    - If in em_qualificacao and has all 5 fields, move to qualificado
    - No auto-transition from qualificado onward (requires explicit action)
    """
    all_fields_complete = (
        lead.name
        and lead.service_interest
        and lead.complaint
        and lead.budget_range.value != "nao_informado"
        and lead.urgency.value != "nao_informada"
    )

    if lead.state == LeadState.novo:
        # Auto-promote if any field filled
        has_any_field = (
            lead.name
            or lead.service_interest
            or lead.complaint
            or lead.budget_range.value != "nao_informado"
            or lead.urgency.value != "nao_informada"
        )
        if has_any_field:
            trans = can_transition(lead.state, LeadState.em_qualificacao)
            if trans.allowed:
                return trans

    if lead.state == LeadState.em_qualificacao:
        # Auto-promote if all 5 complete
        if all_fields_complete:
            trans = can_transition(lead.state, LeadState.qualificado)
            if trans.allowed:
                return trans

    return None
