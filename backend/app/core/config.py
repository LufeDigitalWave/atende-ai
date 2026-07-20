"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
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

    # LLM — Agent chat
    llm_provider: Literal["fake", "claude", "openai"] = "fake"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    agent_model: str = "claude-haiku-4-5"
    agent_prompt_version: str = "sofia_v1"  # legacy; factory v2 uses template directly
    agent_temperature: float = 0.4

    # LLM — Factory (niche profile generation)
    factory_model: str = "gpt-4.1-mini"
    factory_max_niche_chars: int = 60

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

    # Kill switch (operational control without restart)
    kill_switch_chat: bool = True       # False = chat disabled, returns 503
    kill_switch_handoff: bool = True    # False = handoff suppressed (lead stays in qualificado)

    # Budget alerting
    budget_alert_enabled: bool = False
    budget_alert_thresholds: str = "50,80,100"  # comma-separated percentages
    budget_alert_webhook_url: str | None = None
    budget_alert_telegram_token: str | None = None
    budget_alert_telegram_chat_id: str | None = None
    budget_alert_cooldown_hours: int = 6

    @property
    def budget_alert_thresholds_list(self) -> list[int]:
        """Parse comma-separated alert thresholds."""
        return [int(t.strip()) for t in self.budget_alert_thresholds.split(",") if t.strip()]

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

    @model_validator(mode="after")
    def validate_production_secrets(self):
        """Fail fast when production would run with unsafe admin/JWT defaults."""
        if self.environment != "production":
            return self

        if not self.jwt_secret or self.jwt_secret == "change-me-in-production":
            raise ValueError(
                "JWT_SECRET must be set to a non-default value in production"
            )
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production")

        if not self.admin_password or self.admin_password == "admin":
            raise ValueError(
                "ADMIN_PASSWORD must be set to a non-default value in production"
            )
        if len(self.admin_password) < 12:
            raise ValueError("ADMIN_PASSWORD must be at least 12 characters in production")

        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()