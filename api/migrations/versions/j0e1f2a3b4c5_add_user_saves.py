"""Add user_saves table for explicit reader bookmarks of widget state.

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-05-16 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "j0e1f2a3b4c5"
down_revision = "i9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_saves",
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
        sa.Column("widget_title", sa.String(160), nullable=False),
        sa.Column("playbook_title", sa.String(200), nullable=False),
        sa.Column(
            "preview_text",
            sa.String(400),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "saved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "playbook_slug",
            "widget_key",
            name="uq_user_saves_user_slug_widget",
        ),
    )
    op.create_index(
        "ix_user_saves_user_saved_at",
        "user_saves",
        ["user_id", "saved_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_saves_user_saved_at", table_name="user_saves")
    op.drop_table("user_saves")
