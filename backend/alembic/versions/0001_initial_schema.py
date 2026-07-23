"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-13

Creates the full schema for Atende AI:
- pgvector extension
- enums (session_status, message_role, budget_range, urgency, lead_state, lead_event_type, call_type)
- 7 tables: sessions, messages, leads, lead_events, knowledge_chunks, usage_log, admin_users
- indexes (incl. GIN on knowledge_chunks.tsv)
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Enums
    session_status = postgresql.ENUM(
        "active", "capped", "expired", name="session_status", create_type=False
    )
    message_role = postgresql.ENUM(
        "user", "agent", "system_event", name="message_role", create_type=False
    )
    budget_range = postgresql.ENUM(
        "nao_informado",
        "ate_1k",
        "ate_3k",
        "ate_6k",
        "acima_6k",
        name="budget_range",
        create_type=False,
    )
    urgency = postgresql.ENUM(
        "nao_informada",
        "baixa",
        "media",
        "alta",
        name="urgency",
        create_type=False,
    )
    lead_state = postgresql.ENUM(
        "novo",
        "em_qualificacao",
        "qualificado",
        "agendamento_proposto",
        "handoff",
        name="lead_state",
        create_type=False,
    )
    lead_event_type = postgresql.ENUM(
        "session_started",
        "field_extracted",
        "score_updated",
        "state_changed",
        "handoff_triggered",
        "slot_offered",
        "slot_picked",
        "human_requested",
        "out_of_scope",
        "session_capped",
        name="lead_event_type",
        create_type=False,
    )
    call_type = postgresql.ENUM(
        "chat", "extraction", "embedding", name="call_type", create_type=False
    )

    bind = op.get_bind()
    postgresql.ENUM(
        "active", "capped", "expired", name="session_status"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "user", "agent", "system_event", name="message_role"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "nao_informado",
        "ate_1k",
        "ate_3k",
        "ate_6k",
        "acima_6k",
        name="budget_range",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "nao_informada", "baixa", "media", "alta", name="urgency"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "novo",
        "em_qualificacao",
        "qualificado",
        "agendamento_proposto",
        "handoff",
        name="lead_state",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "session_started",
        "field_extracted",
        "score_updated",
        "state_changed",
        "handoff_triggered",
        "slot_offered",
        "slot_picked",
        "human_requested",
        "out_of_scope",
        "session_capped",
        name="lead_event_type",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "chat", "extraction", "embedding", name="call_type"
    ).create(bind, checkfirst=True)

    # sessions
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("message_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "capped",
                "expired",
                name="session_status",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("ip_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_sessions_status", "sessions", ["status"])
    op.create_index("ix_sessions_ip_hash", "sessions", ["ip_hash"])

    # messages
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            postgresql.ENUM(
                "user",
                "agent",
                "system_event",
                name="message_role",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_messages_session_id", "messages", ["session_id"])
    op.create_index("ix_messages_role", "messages", ["role"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # leads
    op.create_table(
        "leads",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("service_interest", sa.String(120), nullable=True),
        sa.Column("complaint", sa.Text, nullable=True),
        sa.Column(
            "budget_range",
            postgresql.ENUM(
                "nao_informado",
                "ate_1k",
                "ate_3k",
                "ate_6k",
                "acima_6k",
                name="budget_range",
                create_type=False,
            ),
            nullable=False,
            server_default="nao_informado",
        ),
        sa.Column(
            "urgency",
            postgresql.ENUM(
                "nao_informada",
                "baixa",
                "media",
                "alta",
                name="urgency",
                create_type=False,
            ),
            nullable=False,
            server_default="nao_informada",
        ),
        sa.Column("score", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "state",
            postgresql.ENUM(
                "novo",
                "em_qualificacao",
                "qualificado",
                "agendamento_proposto",
                "handoff",
                name="lead_state",
                create_type=False,
            ),
            nullable=False,
            server_default="novo",
        ),
        sa.Column(
            "score_breakdown",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("scheduled_slot", sa.String(120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_leads_session_id", "leads", ["session_id"], unique=True)
    op.create_index("ix_leads_state", "leads", ["state"])
    op.create_index("ix_leads_updated_at", "leads", ["updated_at"])

    # lead_events
    op.create_table(
        "lead_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "lead_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                "session_started",
                "field_extracted",
                "score_updated",
                "state_changed",
                "handoff_triggered",
                "slot_offered",
                "slot_picked",
                "human_requested",
                "out_of_scope",
                "session_capped",
                name="lead_event_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_lead_events_lead_id", "lead_events", ["lead_id"])
    op.create_index("ix_lead_events_event_type", "lead_events", ["event_type"])
    op.create_index("ix_lead_events_created_at", "lead_events", ["created_at"])

    # knowledge_chunks (pgvector + tsvector fallback)
    op.create_table(
        "knowledge_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.Column("tsv", postgresql.TSVECTOR, nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("source_file", "chunk_index", name="ix_knowledge_source_idx"),
    )
    op.create_index(
        "ix_knowledge_source_file", "knowledge_chunks", ["source_file"]
    )
    op.create_index(
        "ix_knowledge_tsv",
        "knowledge_chunks",
        ["tsv"],
        postgresql_using="gin",
    )

    # usage_log
    op.create_table(
        "usage_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "call_type",
            postgresql.ENUM(
                "chat",
                "extraction",
                "embedding",
                name="call_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cached_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "cost_usd",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_usage_log_session_id", "usage_log", ["session_id"])
    op.create_index("ix_usage_log_call_type", "usage_log", ["call_type"])
    op.create_index("ix_usage_log_created_at", "usage_log", ["created_at"])

    # admin_users
    op.create_table(
        "admin_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("admin_users")
    op.drop_table("usage_log")
    op.drop_table("knowledge_chunks")
    op.drop_table("lead_events")
    op.drop_table("leads")
    op.drop_table("messages")
    op.drop_table("sessions")

    op.execute("DROP TYPE IF EXISTS call_type")
    op.execute("DROP TYPE IF EXISTS lead_event_type")
    op.execute("DROP TYPE IF EXISTS lead_state")
    op.execute("DROP TYPE IF EXISTS urgency")
    op.execute("DROP TYPE IF EXISTS budget_range")
    op.execute("DROP TYPE IF EXISTS message_role")
    op.execute("DROP TYPE IF EXISTS session_status")
    op.execute("DROP EXTENSION IF EXISTS vector")
