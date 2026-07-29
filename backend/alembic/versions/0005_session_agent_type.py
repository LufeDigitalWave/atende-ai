"""add agent_type and niche to sessions

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-29

Adds agent_type (varchar 32, default 'sdr') and niche (varchar 100) to sessions table.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("agent_type", sa.String(32), nullable=False, server_default="sdr"))
    op.add_column("sessions", sa.Column("niche", sa.String(100), nullable=True))
    op.create_index("ix_sessions_agent_type", "sessions", ["agent_type"])


def downgrade() -> None:
    op.drop_index("ix_sessions_agent_type", "sessions")
    op.drop_column("sessions", "niche")
    op.drop_column("sessions", "agent_type")
