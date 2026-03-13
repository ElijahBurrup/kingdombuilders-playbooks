"""Make playbook_feedback.playbook_id nullable

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa

revision = "g7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "playbook_feedback",
        "playbook_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "playbook_feedback",
        "playbook_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
