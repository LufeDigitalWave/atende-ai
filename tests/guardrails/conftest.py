"""Shared fixtures for guardrail tests."""
import pytest

from app.services.rate_limit import RateLimiter
from app.services import killswitch


@pytest.fixture
def limiter():
    """Fresh rate limiter per test."""
    return RateLimiter(msg_per_session_secs=2.0, new_sessions_per_ip_per_hour=50)


@pytest.fixture(autouse=True)
def clear_killswitch():
    """Reset kill switch overrides between tests."""
    killswitch.clear_overrides()
    yield
    killswitch.clear_overrides()
