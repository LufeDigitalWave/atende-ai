"""Embedder ABC — abstração para embeddings (Voyage ou fake hash)."""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from app.core.config import get_settings


class Embedder(ABC):
    """Abstract embedder."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Embed text into vector (1024 dims)."""
        pass


class FakeEmbedder(Embedder):
    """Deterministic hash-based embedder for offline/testing."""

    async def embed(self, text: str) -> list[float]:
        h = hashlib.md5(text.encode()).digest()
        # MD5 = 16 bytes, repeat pra 64 bytes → 512 floats
        # Pad pra 1024 com zeros
        embedding = [float(b) / 255.0 for b in (h * 4)]
        embedding.extend([0.0] * (1024 - len(embedding)))
        return embedding[:1024]


class VoyageEmbedder(Embedder):
    """Voyage API embedder."""

    def __init__(self, api_key: str, model: str = "voyage-3"):
        self.api_key = api_key
        self.model = model
        self.client = None  # lazy init

    async def embed(self, text: str) -> list[float]:
        # TODO: implement Voyage API call
        # For now, fallback to fake
        return await FakeEmbedder().embed(text)


def get_embedder() -> Embedder:
    """Factory."""
    settings = get_settings()
    if settings.embedding_provider == "voyage":
        if not settings.voyage_api_key:
            raise RuntimeError("EMBEDDING_PROVIDER=voyage but VOYAGE_API_KEY not set")
        return VoyageEmbedder(settings.voyage_api_key, settings.embedding_model)
    return FakeEmbedder()
