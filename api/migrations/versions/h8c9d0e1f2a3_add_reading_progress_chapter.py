"""Add last_chapter and downloaded to reading_progress

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa

revision = "h8c9d0e1f2a3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reading_progress",
        sa.Column("last_chapter", sa.String(), nullable=True),
    )
    op.add_column(
        "reading_progress",
        sa.Column(
            "downloaded",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("reading_progress", "downloaded")
    op.drop_column("reading_progress", "last_chapter")
