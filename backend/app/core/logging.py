"""Structured logging setup using structlog.

Includes PII sanitization processor for production to comply with LGPD.
"""
from __future__ import annotations

import logging
import re
import sys

import structlog

from app.core.config import get_settings

# PII patterns to scrub in production logs
_PII_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b(?:\+?55\s?)?\(?\d{2}\)?[\s.-]?\d{4,5}[\s.-]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), "[CPF]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),
]


def _scrub_pii(logger, method_name, event_dict):
    """Sanitize PII from log event values in production."""
    settings = get_settings()
    if not settings.is_production:
        return event_dict

    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            for pattern, replacement in _PII_PATTERNS:
                value = pattern.sub(replacement, value)
            event_dict[key] = value
    return event_dict


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=False),
            _scrub_pii,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if not settings.is_production else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "atende") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
