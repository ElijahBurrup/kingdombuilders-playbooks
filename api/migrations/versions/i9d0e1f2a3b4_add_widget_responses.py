"""Add widget_responses table for per-user widget state.

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-05-14 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "i9d0e1f2a3b4"
down_revision = "h8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "widget_responses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("playbook_slug", sa.String(120), nullable=False),
        sa.Column("widget_key", sa.String(80), nullable=False),
        sa.Column(
            "is_history",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("data", postgresql.JSONB(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_widget_responses_user_playbook_widget",
        "widget_responses",
        ["user_id", "playbook_slug", "widget_key"],
    )
    op.create_index(
        "ix_widget_responses_user_history",
        "widget_responses",
        ["user_id", "widget_key", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_widget_responses_user_history", table_name="widget_responses")
    op.drop_index(
        "ix_widget_responses_user_playbook_widget", table_name="widget_responses"
    )
    op.drop_table("widget_responses")
