"""Guardrail: PII sanitizer — phone, email, CPF do not appear in production logs."""
from unittest.mock import patch

from app.core.logging import _scrub_pii


def _make_production():
    """Mock settings to simulate production environment."""
    class FakeSettings:
        is_production = True
    return FakeSettings()


def _make_development():
    class FakeSettings:
        is_production = False
    return FakeSettings()


def test_phone_scrubbed_in_production():
    """Brazilian phone numbers are replaced with [PHONE]."""
    with patch("app.core.logging.get_settings", return_value=_make_production()):
        event = {"event": "user said", "message": "Meu número é +55 11 91328-9497"}
        result = _scrub_pii(None, None, event)
        assert "91328" not in result["message"]
        assert "[PHONE]" in result["message"]


def test_email_scrubbed_in_production():
    """Email addresses are replaced with [EMAIL]."""
    with patch("app.core.logging.get_settings", return_value=_make_production()):
        event = {"event": "contact", "email": "luiz23.lfsc@gmail.com"}
        result = _scrub_pii(None, None, event)
        assert "gmail" not in result["email"]
        assert "[EMAIL]" in result["email"]


def test_cpf_scrubbed_in_production():
    """CPF numbers are replaced with [CPF]."""
    with patch("app.core.logging.get_settings", return_value=_make_production()):
        event = {"event": "lead data", "cpf": "123.456.789-00"}
        result = _scrub_pii(None, None, event)
        assert "123.456" not in result["cpf"]
        assert "[CPF]" in result["cpf"]


def test_pii_not_scrubbed_in_development():
    """PII is NOT scrubbed in development (for debugging)."""
    with patch("app.core.logging.get_settings", return_value=_make_development()):
        event = {"event": "test", "phone": "+55 11 91328-9497"}
        result = _scrub_pii(None, None, event)
        assert "91328" in result["phone"]


def test_ip_scrubbed_in_production():
    """IP addresses are replaced with [IP]."""
    with patch("app.core.logging.get_settings", return_value=_make_production()):
        event = {"event": "request", "client": "192.168.1.100"}
        result = _scrub_pii(None, None, event)
        assert "192.168" not in result["client"]
        assert "[IP]" in result["client"]
