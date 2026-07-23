"""FastAPI application entrypoint.

Wiring:
- CORS
- Startup (DB pool, prompt load, env validation)
- Routes (chat, admin, meta)
- SSE streaming
"""
from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.database import dispose_engine, get_engine
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("main")
settings = get_settings()

app = FastAPI(
    title="Atende AI",
    version="0.1.0",
    description="Demo público de agente SDR de IA — Clínica Renova",
)

# Security headers (defense-in-depth for /api/ responses)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

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

    # Defense-in-depth: Settings already validates this, but keep startup
    # checks explicit so production fails with an operator-friendly message.
    if settings.is_production:
        if not settings.jwt_secret or settings.jwt_secret == "change-me-in-production":
            raise RuntimeError("JWT_SECRET must be set to a non-default value in production")
        if len(settings.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters in production")
        if not settings.admin_password or settings.admin_password == "admin":
            raise RuntimeError("ADMIN_PASSWORD must be set to a non-default value in production")
        if len(settings.admin_password) < 12:
            raise RuntimeError("ADMIN_PASSWORD must be at least 12 characters in production")

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
from datetime import UTC

from app.api import routes_admin, routes_chat

app.include_router(routes_chat.router)
app.include_router(routes_admin.router)


@app.get("/api/health")
async def health_check():
    """Simple health check."""
    from datetime import datetime

    return {
        "status": "ok",
        "environment": settings.environment,
        "provider": settings.llm_provider,
        "timestamp": datetime.now(UTC).isoformat(),
    }
