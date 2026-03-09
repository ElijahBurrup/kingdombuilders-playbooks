"""Add playbook_tags and playbook_connections tables for discovery engine

Revision ID: a1b2c3d4e5f6
Revises: cd7bd8051532
Create Date: 2026-03-08 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "cd7bd8051532"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playbook_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("playbook_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), server_default=sa.text("1.0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["playbook_id"], ["playbooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("playbook_id", "tag", name="uq_playbook_tag"),
    )
    op.create_index("ix_playbook_tags_playbook_id", "playbook_tags", ["playbook_id"])
    op.create_index("ix_playbook_tags_tag", "playbook_tags", ["tag"])

    op.create_table(
        "playbook_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_type", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("teaser", sa.String(), nullable=False),
        sa.Column("strength", sa.Float(), server_default=sa.text("0.8"), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["playbooks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["playbooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "target_id", "connection_type", name="uq_playbook_connection"),
    )
    op.create_index("ix_playbook_connections_source_id", "playbook_connections", ["source_id"])
    op.create_index("ix_playbook_connections_target_id", "playbook_connections", ["target_id"])


def downgrade() -> None:
    op.drop_table("playbook_connections")
    op.drop_table("playbook_tags")
