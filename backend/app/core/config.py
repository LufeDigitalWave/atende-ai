"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    contact_url: str = "https://wa.me/5511999999999"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://atende:atende@db:5432/atende_ai"
    )

    # LLM
    llm_provider: Literal["fake", "claude", "openai"] = "fake"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    agent_model: str = "claude-haiku-4-5"
    agent_prompt_version: str = "sofia_v1"
    agent_temperature: float = 0.4

    # Embeddings
    embedding_provider: Literal["fake", "voyage"] = "fake"
    voyage_api_key: str | None = None
    embedding_model: str = "voyage-3"
    embedding_dim: int = 1024  # voyage-3 default

    # Budget / guards
    daily_token_budget: int = 200_000
    max_messages_per_session: int = 30
    rate_limit_seconds: float = 2.0
    rate_limit_new_sessions_per_ip_hour: int = 5
    max_input_chars: int = 500
    session_ttl_hours: int = 24

    # Admin
    admin_username: str = "admin"
    admin_password: str = "admin"
    jwt_secret: str = "change-me-in-production"
    jwt_expires_hours: int = 24

    # CORS (comma-separated string in env, parsed to list)
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("anthropic_api_key")
    @classmethod
    def require_api_key_for_claude(cls, v, info):
        # Allow None for fake provider; require non-empty for claude.
        # This validator runs together with the other fields; we don't have
        # access to llm_provider here, so we just return v as-is. The startup
        # check in main.py performs the actual fail-fast.
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()