"""Common Pydantic schemas shared across endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ErrorResponse(BaseSchema):
    detail: str
    code: str | None = None
    extra: dict[str, Any] | None = None


class BannerResponse(BaseSchema):
    type: str
    message: str
    url: str | None = None


class HealthResponse(BaseSchema):
    status: str
    environment: str
    provider: str
    timestamp: datetime