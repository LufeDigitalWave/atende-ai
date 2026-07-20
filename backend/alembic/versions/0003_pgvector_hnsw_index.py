"""Add HNSW index for pgvector embedding similarity search.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-20
"""
from alembic import op


# revision identifiers
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HNSW index for cosine distance — dramatically speeds up
    # ORDER BY embedding <-> query_vector LIMIT k queries.
    # Default params: m=16, ef_construction=64 (good for <100k rows).
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_embedding_hnsw "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_embedding_hnsw")
