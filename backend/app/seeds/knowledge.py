"""Seed the knowledge base from markdown files into PostgreSQL + pgvector.

Usage: python -m app.seeds.knowledge
"""
import asyncio
import hashlib
from pathlib import Path

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import Base, get_engine, get_session_factory
from app.core.logging import configure_logging, get_logger
from app.models import KnowledgeChunk
from app.services.embedder import get_embedder

configure_logging()
logger = get_logger("seed_knowledge")


KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into chunks with overlap."""
    chunks = []
    words = text.split()
    current_chunk = []
    current_size = 0

    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1
        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap:] if overlap else []
            current_size = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c.strip() for c in chunks if c.strip()]


async def load_and_seed_knowledge(session: AsyncSession) -> None:
    """Load all .md files and seed into DB."""
    settings = get_settings()
    embedder = get_embedder()

    # Clear existing chunks (idempotent)
    await session.execute(delete(KnowledgeChunk))
    await session.commit()
    logger.info("cleared existing knowledge chunks")

    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        logger.warning(f"no markdown files found in {KNOWLEDGE_DIR}")
        return

    total_chunks = 0

    for file_path in md_files:
        try:
            text = file_path.read_text(encoding="utf-8")
            filename = file_path.name
            chunks = chunk_text(text, chunk_size=500, overlap=50)

            for chunk_idx, chunk_text_str in enumerate(chunks):
                # Get embedding
                embedding = None

                if settings.embedding_provider == "voyage":
                    embedding = await embedder.embed(chunk_text_str)
                elif settings.embedding_provider == "fake":
                    # Hash-based fake embedding for deterministic testing
                    h = hashlib.md5(chunk_text_str.encode()).digest()
                    embedding = [float(b) / 255.0 for b in h[:64]]
                    embedding.extend([0.0] * (1024 - len(embedding)))

                # Create record
                chunk = KnowledgeChunk(
                    source_file=filename,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_text_str,
                    embedding=embedding if embedding else None,
                    metadata_={
                        "file": filename,
                        "chunk_size": len(chunk_text_str),
                    },
                )
                session.add(chunk)
                total_chunks += 1

            await session.commit()
            logger.info(f"seeded {filename} ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"failed to seed {file_path}: {e}")
            raise

    logger.info(f"knowledge base seeded: {total_chunks} total chunks")


async def main() -> None:
    """Entry point for `python -m app.seeds.knowledge`."""
    engine = get_engine()
    factory = get_session_factory()

    # Create tables (idempotent if alembic already ran)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("tables created/verified")

    # Seed knowledge
    async with factory() as session:
        await load_and_seed_knowledge(session)

    await engine.dispose()
    logger.info("seed complete")


if __name__ == "__main__":
    asyncio.run(main())