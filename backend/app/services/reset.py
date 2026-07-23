"""Daily reset job — soft-delete old sessions + re-seed knowledge.

Runs at 03:00 local time each day.
Soft-deletes sessions (sets deleted_at) instead of hard DELETE since Sprint 5.
"""
import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_engine, get_session_factory
from app.core.logging import configure_logging, get_logger
from app.models import Message, Session, UsageLog
from app.services.rate_limit import get_rate_limiter

configure_logging()
logger = get_logger("reset_job")


async def cleanup_old_sessions(session: AsyncSession, ttl_hours: int = 24) -> int:
    """
    Soft-delete sessions older than ttl_hours (sets deleted_at instead of DELETE).

    Returns: number of sessions soft-deleted
    """
    cutoff = datetime.now(UTC) - timedelta(hours=ttl_hours)
    now = datetime.now(UTC)
    stmt = (
        update(Session)
        .where(Session.last_activity_at < cutoff, Session.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount or 0


async def cleanup_orphan_records(session: AsyncSession) -> tuple[int, int, int]:
    """
    Delete messages, usage_log, etc. that reference deleted sessions.

    Returns: (messages_deleted, usage_logs_deleted, other_deleted)
    """
    # Get all valid session IDs
    valid_sessions = await session.execute(select(Session.id))
    valid_ids = {row[0] for row in valid_sessions}

    # Delete messages from invalid sessions
    msg_stmt = delete(Message).where(~Message.session_id.in_(valid_ids))
    msg_result = await session.execute(msg_stmt)
    msg_count = msg_result.rowcount or 0

    # Delete usage_log from invalid sessions
    usage_stmt = delete(UsageLog).where(~UsageLog.session_id.in_(valid_ids))
    usage_result = await session.execute(usage_stmt)
    usage_count = usage_result.rowcount or 0

    await session.commit()
    return msg_count, usage_count, 0


async def reseed_knowledge(session: AsyncSession) -> None:
    """Re-seed knowledge base (idempotent).

    Knowledge chunks are static, so we just re-insert with ON CONFLICT DO NOTHING.
    """
    # Import here to avoid circular dependency
    from app.seeds.knowledge import load_and_seed_knowledge

    try:
        await load_and_seed_knowledge(session)
        logger.info("knowledge base re-seeded")
    except Exception as e:
        logger.error(f"failed to re-seed knowledge: {e}")


async def reset_rate_limiter() -> None:
    """Clear in-memory rate limiter state."""
    limiter = get_rate_limiter()
    limiter.cleanup()
    logger.info("rate limiter cleared")


async def run_daily_reset(ttl_hours: int = 24) -> dict:
    """
    Main reset job.

    Args:
        ttl_hours: sessions older than this are deleted

    Returns: summary dict
    """
    engine = get_engine()
    factory = get_session_factory()

    summary = {
        "sessions_deleted": 0,
        "messages_deleted": 0,
        "usage_logs_deleted": 0,
    }

    try:
        async with factory() as session:
            # 1. Cleanup old sessions
            sessions_deleted = await cleanup_old_sessions(session, ttl_hours)
            summary["sessions_deleted"] = sessions_deleted
            logger.info(f"deleted {sessions_deleted} old sessions")

            # 2. Cleanup orphan records
            msg_del, usage_del, other_del = await cleanup_orphan_records(session)
            summary["messages_deleted"] = msg_del
            summary["usage_logs_deleted"] = usage_del
            logger.info(f"deleted {msg_del} messages, {usage_del} usage logs")

            # 3. Re-seed knowledge (idempotent)
            await reseed_knowledge(session)

            # 4. Clear rate limiter
            reset_rate_limiter()

    finally:
        await engine.dispose()

    logger.info(f"reset job complete: {summary}")
    return summary


if __name__ == "__main__":
    # Entrypoint for `python -m app.services.reset`
    asyncio.run(run_daily_reset())
