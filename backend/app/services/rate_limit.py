"""Rate limiting — in-memory per session and per IP.

Guards:
1. 1 msg/2s per session (rate_limit_seconds)
2. 5 new sessions per IP per hour (rate_limit_new_sessions_per_ip_hour)
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID


class RateLimiter:
    """In-memory rate limiter."""

    def __init__(
        self,
        msg_per_session_secs: float = 2.0,
        new_sessions_per_ip_per_hour: int = 5,
    ):
        self.msg_per_session_secs = msg_per_session_secs
        self.new_sessions_per_ip_per_hour = new_sessions_per_ip_per_hour

        # Per-session rate limit: {session_id: timestamp_of_last_msg}
        self.session_last_msg: dict[UUID, float] = {}

        # Per-IP session creation: {ip_hash: [timestamps_of_sessions_created]}
        self.ip_session_times: dict[str, list[float]] = defaultdict(list)

    def check_session_rate_limit(self, session_id: UUID) -> tuple[bool, str]:
        """
        Check if session can send a message now.

        Returns: (allowed, reason)
        """
        now = time.time()
        last_msg_time = self.session_last_msg.get(session_id)

        if last_msg_time is None:
            # First message in session
            self.session_last_msg[session_id] = now
            return True, ""

        elapsed = now - last_msg_time
        if elapsed < self.msg_per_session_secs:
            wait_time = self.msg_per_session_secs - elapsed
            return False, f"please wait {wait_time:.1f}s before next message"

        self.session_last_msg[session_id] = now
        return True, ""

    def record_new_session(self, ip_hash: str) -> tuple[bool, str]:
        """
        Record a new session creation for an IP.

        Returns: (allowed, reason)
        """
        now = time.time()
        one_hour_ago = now - 3600

        # Prune old entries
        self.ip_session_times[ip_hash] = [
            t for t in self.ip_session_times[ip_hash] if t > one_hour_ago
        ]

        # Check limit
        recent_sessions = len(self.ip_session_times[ip_hash])
        if recent_sessions >= self.new_sessions_per_ip_per_hour:
            return (
                False,
                f"too many sessions from your IP ({recent_sessions}/{self.new_sessions_per_ip_per_hour} per hour)",
            )

        # Record
        self.ip_session_times[ip_hash].append(now)
        return True, ""

    def cleanup(self, session_id: UUID | None = None) -> None:
        """Clean up old entries. Called by reset job."""
        if session_id:
            self.session_last_msg.pop(session_id, None)
        else:
            # Full cleanup (reset job)
            self.session_last_msg.clear()
            self.ip_session_times.clear()


# Global limiter instance
_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        from app.core.config import get_settings

        settings = get_settings()
        _limiter = RateLimiter(
            msg_per_session_secs=settings.rate_limit_seconds,
            new_sessions_per_ip_per_hour=settings.rate_limit_new_sessions_per_ip_hour,
        )
    return _limiter
