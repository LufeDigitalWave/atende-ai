"""Admin routes — login, conversas, leads, custos, agente.

All routes require JWT auth.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, verify_password, hash_password
from app.core.config import get_settings
from app.models import AdminUser, Session, Lead, LeadState, UsageLog
from app.schemas.chat import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSessionSummary,
    AdminSessionsList,
    AdminCostsResponse,
    AdminCostsToday,
    AdminCostsBudget,
    AdminAgentInfo,
)
from app.services.budget import get_daily_usage, get_daily_usage_detailed

logger = structlog.get_logger("routes_admin")
router = APIRouter(prefix="/api/admin", tags=["admin"])
settings = get_settings()


_bearer = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Validate JWT from Authorization header and return admin user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token subject",
        )

    user = await db.scalar(select(AdminUser).where(AdminUser.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found or inactive",
        )

    return user


@router.post(
    "/login",
    response_model=AdminLoginResponse,
)
async def admin_login(
    body: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminLoginResponse:
    """
    Admin login — returns JWT token.
    """
    # Find admin user
    user = await db.scalar(
        select(AdminUser).where(AdminUser.username == body.username)
    )

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user inactive",
        )

    # Create token
    token = create_access_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.jwt_expires_hours
    )

    logger.info(f"admin login: {user.username}")

    return AdminLoginResponse(
        token=token,
        expires_at=expires_at,
    )


@router.get(
    "/conversas",
    response_model=AdminSessionsList,
)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> AdminSessionsList:
    """
    List all sessions with pagination.
    """
    # Count total
    total = await db.scalar(select(func.count()).select_from(Session))

    # Fetch paginated with eager-loaded lead
    stmt = (
        select(Session)
        .options(selectinload(Session.lead))
        .order_by(desc(Session.created_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = await db.scalars(stmt)

    items = [
        AdminSessionSummary(
            session_id=s.id,
            created_at=s.created_at,
            last_activity_at=s.last_activity_at,
            message_count=s.message_count,
            status=s.status,
            lead_name=s.lead.name if s.lead else None,
            lead_state=s.lead.state if s.lead else None,
            lead_score=s.lead.score if s.lead else None,
        )
        for s in sessions
    ]

    return AdminSessionsList(total=total or 0, items=items)


@router.get(
    "/leads",
    response_model=dict,
)
async def get_leads_kanban(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """
    Get leads grouped by state (kanban view).
    """
    result = {
        "novo": [],
        "em_qualificacao": [],
        "qualificado": [],
        "agendamento_proposto": [],
        "handoff": [],
    }

    for state in LeadState:
        leads = list((await db.scalars(
            select(Lead).where(Lead.state == state).order_by(desc(Lead.updated_at))
        )).all())
        result[state.value] = [
            {
                "id": str(lead.id),
                "name": lead.name,
                "service_interest": lead.service_interest,
                "score": lead.score,
                "state": lead.state.value if lead.state else "novo",
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            }
            for lead in leads
        ]

    return result


@router.get(
    "/custos",
    response_model=AdminCostsResponse,
)
async def get_costs(
    days: int = 14,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> AdminCostsResponse:
    """
    Get cost breakdown and budget status.
    """
    # Today's detailed usage
    usage = await get_daily_usage_detailed(db)
    cost_brl = usage["cost_usd"] * 5  # 1 USD ≈ 5 BRL

    today = AdminCostsToday(
        calls=usage["calls"],
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        cached_tokens=usage["cached_tokens"],
        cost_usd=usage["cost_usd"],
        cost_brl=cost_brl,
    )

    # History (last N days)
    from datetime import date as date_type, timedelta as td
    history = []
    for i in range(1, days + 1):
        d = date_type.today() - td(days=i)
        day_usage = await get_daily_usage_detailed(db, d)
        if day_usage["calls"] > 0:
            history.append({
                "date": d.isoformat(),
                "calls": day_usage["calls"],
                "cost_brl": day_usage["cost_usd"] * 5,
            })

    # Budget
    total_tokens = usage["input_tokens"] + usage["output_tokens"]
    budget = AdminCostsBudget(
        daily_tokens=settings.daily_token_budget,
        used_today=total_tokens,
        percent_used=round(100 * total_tokens / max(settings.daily_token_budget, 1), 2),
    )

    return AdminCostsResponse(
        today=today,
        history=history,
        budget=budget,
    )


@router.get(
    "/agente",
    response_model=AdminAgentInfo,
)
async def get_agent_info(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> AdminAgentInfo:
    """
    Get current agent configuration.
    """
    return AdminAgentInfo(
        provider=settings.llm_provider,
        model=settings.agent_model,
        prompt_version=settings.agent_prompt_version,
        prompt_sha256="",  # TODO: compute hash of prompt file
        temperature=settings.agent_temperature,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model if settings.embedding_provider != "fake" else None,
    )
