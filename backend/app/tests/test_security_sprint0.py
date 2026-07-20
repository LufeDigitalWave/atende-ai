"""Sprint 0 security regression tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services.retriever import TsvectorRetriever


class FakeSession:
    """Minimal async session capturing SQL text and params."""

    def __init__(self):
        self.statement = None
        self.params = None

    async def execute(self, statement, params=None):
        self.statement = str(statement)
        self.params = params or {}
        return []


@pytest.mark.asyncio
async def test_tsvector_retriever_parameterizes_keywords():
    """User-controlled query text must never be interpolated into raw SQL."""
    session = FakeSession()
    retriever = TsvectorRetriever()
    payload = "x'; DROP TABLE knowledge_chunks; --"

    results = await retriever.retrieve(session, payload, top_k=3)

    assert results == []
    assert "DROP TABLE" not in session.statement
    assert any(
        isinstance(value, str) and "drop" in value.lower()
        for value in session.params.values()
    )
    assert session.params["limit"] == 3


def test_production_rejects_default_jwt_secret():
    """Production must fail fast if JWT_SECRET is the public default."""
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(
            _env_file=None,
            environment="production",
            jwt_secret="change-me-in-production",
            admin_password="strong-admin-password",
        )


def test_production_rejects_default_admin_password():
    """Production must fail fast if ADMIN_PASSWORD is the public default."""
    with pytest.raises(ValidationError, match="ADMIN_PASSWORD"):
        Settings(
            _env_file=None,
            environment="production",
            jwt_secret="x" * 32,
            admin_password="admin",
        )


def test_production_accepts_strong_security_settings():
    """Strong production secrets should pass Settings validation."""
    settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret="x" * 32,
        admin_password="strong-admin-password",
    )

    assert settings.is_production
    assert settings.jwt_secret == "x" * 32
