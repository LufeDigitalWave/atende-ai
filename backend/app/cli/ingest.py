"""CLI tool for ingesting knowledge base files into a namespace.

Usage:
    python -m app.cli.ingest --namespace <client_name> --path <dir_or_file>
    python -m app.cli.ingest --namespace acme --path /data/acme/docs/
    python -m app.cli.ingest --namespace default --path app/seeds/knowledge/

Idempotent: re-running with the same namespace+source_file+chunk_index
will update existing chunks (upsert by unique index).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def chunk_text(text: str, max_chars: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


async def ingest(namespace: str, path: Path, clear_first: bool = False) -> int:
    """Ingest markdown/text files into knowledge_chunks for a namespace."""
    from sqlalchemy import delete, select

    from app.core.database import get_engine, get_session_factory
    from app.models.knowledge import KnowledgeChunk
    from app.services.embedder import get_embedder

    engine = get_engine()
    factory = get_session_factory()
    embedder = get_embedder()

    files: list[Path] = []
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("*.md")) + sorted(path.glob("*.txt"))
    else:
        print(f"ERROR: {path} does not exist")
        return 0

    if not files:
        print(f"WARNING: no .md or .txt files found in {path}")
        return 0

    total_chunks = 0

    async with factory() as session:
        if clear_first:
            await session.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.namespace == namespace)
            )
            await session.commit()
            print(f"Cleared existing chunks for namespace '{namespace}'")

        for file in files:
            content = file.read_text(encoding="utf-8")
            chunks = chunk_text(content)
            source_name = file.name

            for idx, chunk in enumerate(chunks):
                # Upsert: check if exists
                existing = await session.scalar(
                    select(KnowledgeChunk).where(
                        KnowledgeChunk.namespace == namespace,
                        KnowledgeChunk.source_file == source_name,
                        KnowledgeChunk.chunk_index == idx,
                    )
                )

                embedding = await embedder.embed(chunk)

                if existing:
                    existing.chunk_text = chunk
                    existing.embedding = embedding
                else:
                    new_chunk = KnowledgeChunk(
                        namespace=namespace,
                        source_file=source_name,
                        chunk_index=idx,
                        chunk_text=chunk,
                        embedding=embedding,
                    )
                    session.add(new_chunk)

                total_chunks += 1

            await session.commit()
            print(f"  {source_name}: {len(chunks)} chunks")

    print(f"\nDone: {total_chunks} chunks ingested into namespace '{namespace}'")
    return total_chunks


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base files")
    parser.add_argument("--namespace", required=True, help="Namespace/tenant identifier")
    parser.add_argument("--path", required=True, help="Path to directory or file to ingest")
    parser.add_argument("--clear", action="store_true", help="Clear existing chunks for this namespace before ingesting")
    args = parser.parse_args()

    asyncio.run(ingest(args.namespace, Path(args.path), clear_first=args.clear))


if __name__ == "__main__":
    main()
