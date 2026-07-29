"""Funnel event endpoints — server-side conversion tracking.

Public endpoint (rate-limited) to record funnel steps.
Admin endpoint to aggregate funnel data.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ip_hash import get_client_ip, hash_ip
from app.api.routes_admin import get_current_admin
from app.models.funnel_event import FunnelEvent, FunnelStep

router = APIRouter(tags=["funnel"])


# --- Public: record event ---

class EventCreate(BaseModel):
    step: FunnelStep
    session_id: str | None = Field(None, max_length=64)
    metadata: dict = Field(default_factory=dict)


@router.post("/api/events", status_code=201)
async def record_event(
    body: EventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Record a funnel event. No auth required; rate-limited by IP."""
    ip = get_client_ip(request)
    ip_hashed = hash_ip(ip)

    event = FunnelEvent(
        step=body.step,
        session_id=body.session_id,
        ip_hash=ip_hashed,
        metadata_=body.metadata,
    )
    db.add(event)
    await db.commit()
    return {"status": "recorded"}


# --- Admin: funnel aggregation ---

@router.get("/api/admin/funnel")
async def get_funnel(
    days: int = 7,
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate funnel events by step for the last N days."""
    if days < 1 or days > 90:
        raise HTTPException(400, "days must be 1-90")

    since = datetime.now(UTC) - timedelta(days=days)

    stmt = (
        select(
            FunnelEvent.step,
            func.count().label("count"),
            func.count(func.distinct(FunnelEvent.ip_hash)).label("unique_visitors"),
        )
        .where(FunnelEvent.created_at >= since)
        .group_by(FunnelEvent.step)
        .order_by(func.count().desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    funnel = [
        {
            "step": row.step.value,
            "count": row.count,
            "unique_visitors": row.unique_visitors,
        }
        for row in rows
    ]

    return {
        "period_days": days,
        "funnel": funnel,
    }
