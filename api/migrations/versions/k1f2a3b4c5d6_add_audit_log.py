"""Add audit_log table for sign-up + payment + webhook + email pipeline events.

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-05-18 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "k1f2a3b4c5d6"
down_revision = "j0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'success'"),
        ),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider_session_id", sa.String(255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(255), nullable=True),
        sa.Column("provider_payment_id", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_log_email_timestamp",
        "audit_log",
        ["email", "timestamp"],
    )
    op.create_index(
        "ix_audit_log_event_type_timestamp",
        "audit_log",
        ["event_type", "timestamp"],
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index(
        "ix_audit_log_session_id", "audit_log", ["provider_session_id"]
    )
    op.create_index(
        "ix_audit_log_subscription_id", "audit_log", ["provider_subscription_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_subscription_id", table_name="audit_log")
    op.drop_index("ix_audit_log_session_id", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_event_type_timestamp", table_name="audit_log")
    op.drop_index("ix_audit_log_email_timestamp", table_name="audit_log")
    op.drop_table("audit_log")
