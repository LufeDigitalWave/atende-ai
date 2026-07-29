"""Guardrail: rate limit — message interval and session creation."""
import time
from uuid import uuid4

from app.services.rate_limit import RateLimiter


def test_first_message_allowed(limiter: RateLimiter):
    """First message in a session is always allowed."""
    allowed, reason = limiter.check_session_rate_limit(uuid4())
    assert allowed is True
    assert reason == ""


def test_immediate_second_message_denied(limiter: RateLimiter):
    """Second message within 2s is denied with 429-like reason."""
    session_id = uuid4()
    limiter.check_session_rate_limit(session_id)
    allowed, reason = limiter.check_session_rate_limit(session_id)
    assert allowed is False
    assert "wait" in reason.lower()


def test_message_allowed_after_interval(limiter: RateLimiter):
    """Message allowed after waiting the interval."""
    session_id = uuid4()
    limiter.check_session_rate_limit(session_id)
    # Simulate time passing by directly manipulating the timestamp
    limiter.session_last_msg[session_id] = time.time() - 3.0
    allowed, reason = limiter.check_session_rate_limit(session_id)
    assert allowed is True


def test_session_creation_within_limit(limiter: RateLimiter):
    """Creating sessions up to the limit is allowed."""
    ip = "hash_test_ip"
    for _ in range(50):
        allowed, _ = limiter.record_new_session(ip)
        assert allowed is True


def test_session_51_denied(limiter: RateLimiter):
    """51st session from same IP is denied."""
    ip = "hash_test_ip_51"
    for _ in range(50):
        limiter.record_new_session(ip)
    allowed, reason = limiter.record_new_session(ip)
    assert allowed is False
    assert "too many sessions" in reason.lower()
