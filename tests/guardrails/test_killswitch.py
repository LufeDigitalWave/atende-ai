"""Guardrail: kill switch — demo returns refusal when toggled off."""
from app.services import killswitch


def test_chat_enabled_by_default():
    """Chat component is enabled when no override set."""
    assert killswitch.is_enabled("chat") is True


def test_chat_disabled_after_override():
    """Chat disabled after setting override to False."""
    killswitch.set_override("chat", False)
    assert killswitch.is_enabled("chat") is False


def test_handoff_disabled_after_override():
    """Handoff disabled after setting override to False."""
    killswitch.set_override("handoff", False)
    assert killswitch.is_enabled("handoff") is False


def test_state_reflects_overrides():
    """get_state returns current override values."""
    killswitch.set_override("chat", False)
    killswitch.set_override("handoff", True)
    state = killswitch.get_state()
    assert state["chat"] is False
    assert state["handoff"] is True


def test_clear_overrides_restores_defaults():
    """clear_overrides restores config defaults."""
    killswitch.set_override("chat", False)
    killswitch.clear_overrides()
    assert killswitch.is_enabled("chat") is True
