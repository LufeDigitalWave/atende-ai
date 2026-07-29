"""funnel events table

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-28

Adds funnel_events table for server-side conversion tracking.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    funnel_step = postgresql.ENUM(
        "view_landing",
        "start_demo",
        "first_message",
        "reached_qualified",
        "lead_captured",
        "clicked_pricing",
        "clicked_whatsapp",
        name="funnel_step",
        create_type=False,
    )
    funnel_step.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "funnel_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("step", funnel_step, nullable=False, index=True),
        sa.Column("session_id", sa.String(64), nullable=True, index=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("funnel_events")
    op.execute("DROP TYPE IF EXISTS funnel_step")
