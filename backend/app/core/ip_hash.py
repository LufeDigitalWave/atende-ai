"""IP hashing for LGPD-safe visitor tracking.

The salt is taken from JWT_SECRET to keep it stable per deployment
but unpredictable across deployments.
"""
from __future__ import annotations

import hashlib

from fastapi import Request

from app.core.config import get_settings


def hash_ip(ip: str) -> str:
    settings = get_settings()
    h = hashlib.sha256()
    h.update(settings.jwt_secret.encode("utf-8"))
    h.update(b":")
    h.update(ip.encode("utf-8"))
    return h.hexdigest()[:32]


def get_client_ip(request: Request) -> str:
    """Extract the real client IP, honoring X-Forwarded-For when behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry is the original client
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"