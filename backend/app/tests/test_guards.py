"""Test guardrails — budget, rate limit, caps."""
from uuid import uuid4

from app.services.rate_limit import RateLimiter


def test_rate_limiter_first_message_allowed():
    """First message in session is always allowed."""
    limiter = RateLimiter(msg_per_session_secs=2.0)
    session_id = uuid4()
    allowed, reason = limiter.check_session_rate_limit(session_id)
    assert allowed


def test_rate_limiter_second_message_immediate_denied():
    """Second message within 2s is denied."""
    limiter = RateLimiter(msg_per_session_secs=2.0)
    session_id = uuid4()

    # First message
    allowed1, _ = limiter.check_session_rate_limit(session_id)
    assert allowed1

    # Second message immediately
    allowed2, reason = limiter.check_session_rate_limit(session_id)
    assert not allowed2
    assert "wait" in reason.lower()


def test_rate_limiter_new_sessions_per_ip():
    """Max N new sessions per IP per hour."""
    limiter = RateLimiter(new_sessions_per_ip_per_hour=3)
    ip_hash = "test_ip_hash"

    # First 3 sessions allowed
    for i in range(3):
        allowed, reason = limiter.record_new_session(ip_hash)
        assert allowed, f"session {i+1} should be allowed"

    # 4th session denied
    allowed, reason = limiter.record_new_session(ip_hash)
    assert not allowed
    assert "too many" in reason.lower()


def test_rate_limiter_cleanup():
    """Cleanup clears all state."""
    limiter = RateLimiter()
    session_id = uuid4()

    limiter.check_session_rate_limit(session_id)
    limiter.record_new_session("ip_hash")

    # Cleanup
    limiter.cleanup()

    # Should be fresh
    allowed, _ = limiter.check_session_rate_limit(session_id)
    assert allowed
