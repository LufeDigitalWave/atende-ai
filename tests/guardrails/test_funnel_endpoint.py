"""Guardrail: funnel endpoint — rate limit, validation, no PII stored."""
import pytest
from pydantic import ValidationError

from app.api.routes_funnel import EventCreate
from app.models.funnel_event import FunnelStep


def test_valid_event_create():
    """Valid funnel event passes validation."""
    event = EventCreate(step="view_landing", session_id="abc123", metadata={"niche": "clinica"})
    assert event.step == FunnelStep.view_landing
    assert event.session_id == "abc123"


def test_invalid_step_rejected():
    """Invalid funnel step is rejected."""
    with pytest.raises(ValidationError):
        EventCreate(step="invalid_step")


def test_session_id_max_length():
    """Session ID longer than 64 chars is rejected."""
    with pytest.raises(ValidationError):
        EventCreate(step="view_landing", session_id="a" * 65)


def test_all_funnel_steps_valid():
    """All defined funnel steps are accepted."""
    for step in FunnelStep:
        event = EventCreate(step=step.value)
        assert event.step == step


def test_metadata_defaults_to_empty_dict():
    """Metadata defaults to empty dict when not provided."""
    event = EventCreate(step="start_demo")
    assert event.metadata == {}


def test_no_pii_fields_in_model():
    """FunnelEvent model has no name/email/phone/cpf fields (privacy by design)."""
    from app.models.funnel_event import FunnelEvent
    columns = {c.name for c in FunnelEvent.__table__.columns}
    pii_fields = {"name", "email", "phone", "cpf", "telefone"}
    assert columns.isdisjoint(pii_fields), f"PII fields found in FunnelEvent: {columns & pii_fields}"
