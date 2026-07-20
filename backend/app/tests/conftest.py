"""pytest fixtures."""
import asyncio
import os
from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force dev/test env settings BEFORE importing app
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET", "test-secret-must-be-32-chars-long-xx")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password-123")
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.setdefault("EMBEDDING_PROVIDER", "fake")

# Register type adapters for SQLite (it doesn't natively handle UUID/dict/Decimal)
import json as _json
import sqlite3
import uuid as _uuid
from decimal import Decimal as _Decimal

sqlite3.register_adapter(_uuid.UUID, lambda u: str(u))
sqlite3.register_converter("UUID", lambda b: _uuid.UUID(b.decode()))
sqlite3.register_adapter(dict, lambda d: _json.dumps(d))
sqlite3.register_adapter(list, lambda l: _json.dumps(l))
sqlite3.register_adapter(_Decimal, lambda d: str(d))

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Lead, Message, Session, SessionStatus  # noqa: E402
from app.services import llm as llm_module  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """In-memory SQLite engine for the test session.

    Patches PostgreSQL-only types (JSONB, TSVECTOR, Vector, UUID) to their
    SQLite-compatible equivalents so the full schema can be created.
    """
    from sqlalchemy import event, Text, String
    from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
    from sqlalchemy.types import TypeDecorator, UserDefinedType, TEXT

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:?check_same_thread=False",
        echo=False,
        future=True,
        connect_args={"detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES},
    )

    # Render PG types as SQLite-compatible when creating schema
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    async with engine.begin() as conn:
        def _create_all_with_type_overrides(connection):
            # Monkey-patch column types for SQLite compatibility
            for table in Base.metadata.sorted_tables:
                for col in table.columns:
                    type_name = type(col.type).__name__.upper()
                    if type_name == "JSONB" or type_name == "JSON":
                        col.type = Text()
                    elif type_name in ("TSVECTOR", "VECTOR"):
                        col.type = Text()
                    elif type_name == "UUID":
                        col.type = String(36)
                    elif isinstance(col.type, UserDefinedType):
                        col.type = Text()
            Base.metadata.create_all(bind=connection)

        await conn.run_sync(_create_all_with_type_overrides)

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    """Per-test async session with rollback."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(test_engine, monkeypatch) -> AsyncIterator[AsyncClient]:
    """Async HTTP client with DB overridden to in-memory SQLite.

    LLM provider is replaced with FakeLLMProvider for deterministic responses.
    """

    # Override get_db to use the test engine
    # Use NullPool-like behavior: each get_db call gets an independent session
    # that sees committed state from prior calls (important for multi-request tests)
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
    )

    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db

    # Patch the LLM module's factory
    monkeypatch.setattr(llm_module, "get_llm_provider", lambda: llm_module.FakeLLMProvider())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_session(db_session: AsyncSession) -> Session:
    """Pre-create a session row for tests that need an existing session."""
    session = Session(
        status=SessionStatus.active,
        niche="clinica_estetica",
        message_count=0,
    )
    db_session.add(session)
    lead = Lead(state="novo", score=0)
    db_session.add(lead)
    await db_session.flush()
    session.lead_id = lead.id
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def seeded_admin(test_engine, client: AsyncClient) -> str:
    """Create a test admin user (if not exists) and return its JWT token.

    Uses the same in-memory engine as the client fixture so the admin user is
    visible to subsequent admin requests.
    """
    from sqlalchemy import select
    from app.core.security import create_access_token, hash_password
    from app.models import AdminUser

    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        existing = await session.scalar(
            select(AdminUser).where(AdminUser.username == "admin")
        )
        if existing:
            token = create_access_token(str(existing.id))
            return token

        admin = AdminUser(
            username="admin",
            password_hash=hash_password("test-admin-password-123"),
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        token = create_access_token(str(admin.id))
        return token