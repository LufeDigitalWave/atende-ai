"""Guardrail: input max 500 chars — rejected before reaching LLM."""
import pytest
from pydantic import ValidationError

from app.schemas.chat import MessageCreate


def test_500_chars_accepted():
    """Message with exactly 500 chars is accepted."""
    msg = MessageCreate(content="a" * 500)
    assert len(msg.content) == 500


def test_501_chars_rejected():
    """Message with 501 chars is rejected by Pydantic before hitting LLM."""
    with pytest.raises(ValidationError) as exc_info:
        MessageCreate(content="a" * 501)
    errors = exc_info.value.errors()
    assert any("max_length" in str(e).lower() or "500" in str(e) for e in errors)


def test_empty_content_rejected():
    """Empty content after strip is rejected."""
    with pytest.raises(ValidationError):
        MessageCreate(content="   ")


def test_1_char_accepted():
    """Single char is valid (min_length=1)."""
    msg = MessageCreate(content="x")
    assert msg.content == "x"
