"""Budget tracking and enforcement.

Daily token budget cap with usage logging per call.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import UsageLog


class BudgetExceededError(Exception):
    """Raised when daily budget is exhausted."""

    pass


async def log_usage(
    session: AsyncSession,
    session_id: str | None,
    call_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int,
) -> Decimal:
    """
    Log LLM call to usage_log table and compute cost.

    Cost formula (varies by model):
    - GPT-4o-mini: input $0.15/1M, output $0.60/1M
    - GPT-4o: input $5.00/1M, output $15.00/1M
    - Claude Haiku: input $0.75/1M, output $3.75/1M
    - Cached input: 10% of input price

    Returns: cost_usd
    """
    # Pricing by model
    PRICING = {
        "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
        "gpt-4o": (Decimal("5.00"), Decimal("15.00")),
        "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")),
        "gpt-4.1": (Decimal("10.00"), Decimal("30.00")),
        "claude-haiku-4-5": (Decimal("0.75"), Decimal("3.75")),
        "claude-sonnet-4-6": (Decimal("3.00"), Decimal("15.00")),
    }
    input_per_m, output_per_m = PRICING.get(model, (Decimal("1.00"), Decimal("5.00")))
    input_price = input_per_m / Decimal("1000000")
    output_price = output_per_m / Decimal("1000000")
    cache_price = input_price * Decimal("0.1")

    # Compute cost
    cost = (
        input_tokens * input_price
        + output_tokens * output_price
        + cached_tokens * cache_price
    )

    # Log
    log = UsageLog(
        session_id=session_id,
        call_type=call_type,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        cost_usd=cost,
    )
    session.add(log)
    await session.commit()

    return cost


async def get_daily_usage(
    session: AsyncSession, target_date: date | None = None
) -> tuple[int, Decimal]:
    """
    Get aggregated usage for a single day.

    Returns: (total_input_tokens, total_cost_usd)
    """
    if target_date is None:
        target_date = date.today()

    # Query usage_log for today
    start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(
        target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
    )

    stmt = select(
        func.sum(UsageLog.input_tokens).label("total_input"),
        func.sum(UsageLog.output_tokens).label("total_output"),
        func.sum(UsageLog.cached_tokens).label("total_cached"),
        func.sum(UsageLog.cost_usd).label("total_cost"),
    ).where(and_(UsageLog.created_at >= start, UsageLog.created_at < end))

    result = await session.execute(stmt)
    row = result.one()

    total_input = row.total_input or 0
    total_output = row.total_output or 0
    total_cached = row.total_cached or 0
    total_cost = row.total_cost or Decimal("0")

    # Re-compute total tokens (input + output, not cached)
    total_tokens = total_input + total_output

    return total_tokens, total_cost


async def get_daily_usage_detailed(
    session: AsyncSession, target_date: date | None = None
) -> dict:
    """Get detailed aggregated usage for a single day (for admin dashboard)."""
    if target_date is None:
        target_date = date.today()

    start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(
        target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
    )

    stmt = select(
        func.count().label("calls"),
        func.sum(UsageLog.input_tokens).label("input_tokens"),
        func.sum(UsageLog.output_tokens).label("output_tokens"),
        func.sum(UsageLog.cached_tokens).label("cached_tokens"),
        func.sum(UsageLog.cost_usd).label("cost_usd"),
    ).where(and_(UsageLog.created_at >= start, UsageLog.created_at < end))

    result = await session.execute(stmt)
    row = result.one()

    return {
        "calls": row.calls or 0,
        "input_tokens": row.input_tokens or 0,
        "output_tokens": row.output_tokens or 0,
        "cached_tokens": row.cached_tokens or 0,
        "cost_usd": float(row.cost_usd or 0),
    }


async def check_budget(
    session: AsyncSession, projected_tokens: int = 0
) -> tuple[bool, int, int]:
    """
    Check if daily budget allows a new call.

    Args:
        session: DB session
        projected_tokens: estimated tokens the next call will use

    Returns: (allowed: bool, used: int, remaining: int)
    """
    settings = get_settings()
    budget = settings.daily_token_budget

    # Get today's usage
    total_tokens, _ = await get_daily_usage(session)

    used = total_tokens
    remaining = max(0, budget - used)
    allowed = (used + projected_tokens) < budget

    return allowed, used, remaining
