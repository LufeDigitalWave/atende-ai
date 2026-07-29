"""add namespace to knowledge_chunks

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-29

Adds namespace column for tenant/scope isolation in RAG.
Existing chunks get namespace='default'.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("knowledge_chunks", sa.Column("namespace", sa.String(100), nullable=False, server_default="default"))
    op.create_index("ix_knowledge_namespace", "knowledge_chunks", ["namespace"])
    # Replace old unique index with namespace-aware one
    op.drop_index("ix_knowledge_source_idx", "knowledge_chunks")
    op.create_index("ix_knowledge_ns_source_idx", "knowledge_chunks", ["namespace", "source_file", "chunk_index"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_knowledge_ns_source_idx", "knowledge_chunks")
    op.create_index("ix_knowledge_source_idx", "knowledge_chunks", ["source_file", "chunk_index"], unique=True)
    op.drop_index("ix_knowledge_namespace", "knowledge_chunks")
    op.drop_column("knowledge_chunks", "namespace")
