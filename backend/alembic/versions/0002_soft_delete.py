"""Add soft delete columns (deleted_at) to sessions and leads.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("deleted_at", TIMESTAMP(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("deleted_at", TIMESTAMP(timezone=True), nullable=True))
    op.create_index("ix_sessions_deleted_at", "sessions", ["deleted_at"])
    op.create_index("ix_leads_deleted_at", "leads", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_leads_deleted_at", table_name="leads")
    op.drop_index("ix_sessions_deleted_at", table_name="sessions")
    op.drop_column("leads", "deleted_at")
    op.drop_column("sessions", "deleted_at")
