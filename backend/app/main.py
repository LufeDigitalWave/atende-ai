"""FastAPI application entrypoint.

Wiring:
- CORS
- Startup (DB pool, prompt load, env validation)
- Routes (chat, admin, meta)
- SSE streaming
"""
from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import dispose_engine, get_engine, get_session_factory
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("main")
settings = get_settings()

app = FastAPI(
    title="Atende AI",
    version="0.1.0",
    description="Demo público de agente SDR de IA — Clínica Renova",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize engine, validate env, load prompt, seed DB."""
    logger.info(
        f"starting atende-ai (env={settings.environment}, provider={settings.llm_provider})"
    )

    # Test DB connection
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("database connected")
    except Exception as e:
        logger.error(f"database connection failed: {e}")
        raise

    # Validate LLM provider
    if settings.llm_provider == "claude" and not settings.anthropic_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=claude but ANTHROPIC_API_KEY not set. "
            "Provide the key or switch to LLM_PROVIDER=fake"
        )

    # Load prompt (will be done in agent/loop.py)
    logger.info(f"using prompt version: {settings.agent_prompt_version}")

    logger.info("startup complete")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup."""
    logger.info("shutting down")
    await dispose_engine()


# Routes
from app.api import routes_chat, routes_admin

app.include_router(routes_chat.router)
app.include_router(routes_admin.router)


@app.get("/api/health")
async def health_check():
    """Simple health check."""
    from datetime import datetime, timezone

    return {
        "status": "ok",
        "environment": settings.environment,
        "provider": settings.llm_provider,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
