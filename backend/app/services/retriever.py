"""Retriever ABC — abstraction for RAG (pgvector or tsvector fallback)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import KnowledgeChunk
from app.services.embedder import get_embedder


class RetrievalResult:
    """Single chunk result."""

    def __init__(self, chunk_text: str, source_file: str, similarity: float):
        self.chunk_text = chunk_text
        self.source_file = source_file
        self.similarity = similarity

    def __repr__(self) -> str:
        return f"<Result file={self.source_file} sim={self.similarity:.2f}>"


class Retriever(ABC):
    """Abstract retriever."""

    @abstractmethod
    async def retrieve(
        self, session: AsyncSession, query: str, top_k: int = 3
    ) -> list[RetrievalResult]:
        """Retrieve top_k most similar chunks."""
        pass


class PgvectorRetriever(Retriever):
    """Vector similarity search via pgvector."""

    async def retrieve(
        self, session: AsyncSession, query: str, top_k: int = 3
    ) -> list[RetrievalResult]:
        embedder = get_embedder()
        query_embedding = await embedder.embed(query)

        stmt = (
            select(KnowledgeChunk)
            .order_by(KnowledgeChunk.embedding.op("<->")(query_embedding))
            .limit(top_k)
        )
        chunks = await session.scalars(stmt)
        results = []
        for chunk in chunks:
            # Cosine distance (0=same, 2=opposite); convert to similarity
            similarity = 1 - (chunk.embedding.op("<->")(query_embedding) / 2)
            results.append(
                RetrievalResult(
                    chunk_text=chunk.chunk_text,
                    source_file=chunk.source_file,
                    similarity=float(similarity),
                )
            )
        return results


class TsvectorRetriever(Retriever):
    """Full-text search via tsvector (fallback without embeddings)."""

    async def retrieve(
        self, session: AsyncSession, query: str, top_k: int = 3
    ) -> list[RetrievalResult]:
        # Simple keyword match — lower quality but works offline
        # TODO: proper PostgreSQL tsvector rank
        keywords = query.lower().split()
        where_clause = " OR ".join(
            [f"chunk_text ILIKE '%{kw}%'" for kw in keywords]
        )
        stmt = text(
            f"""SELECT chunk_text, source_file, 0.5 as similarity
               FROM knowledge_chunks
               WHERE {where_clause}
               LIMIT :limit"""
        )
        rows = await session.execute(stmt.bindparams(limit=top_k))
        return [
            RetrievalResult(
                chunk_text=row.chunk_text,
                source_file=row.source_file,
                similarity=row.similarity,
            )
            for row in rows
        ]


def get_retriever(provider: str = "auto") -> Retriever:
    """Factory. Auto-selects based on config."""
    if provider == "auto":
        settings = get_settings()
        provider = "pgvector" if settings.embedding_provider != "fake" else "tsvector"

    if provider == "pgvector":
        return PgvectorRetriever()
    return TsvectorRetriever()
