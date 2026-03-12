"""Add referral system tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-12 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referral_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_referral_codes_code", "referral_codes", ["code"])

    op.create_table(
        "referrer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stripe_connect_id", sa.String(), nullable=True),
        sa.Column("connect_status", sa.String(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("tax_info_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("tax_info_collected", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("lifetime_earnings_cents", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("payouts_paused", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("referrer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referred_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("root_referrer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referrer_id", "referred_id", name="uq_referral_pair"),
    )
    op.create_index("ix_referrals_referrer_id", "referrals", ["referrer_id"])
    op.create_index("ix_referrals_referred_id", "referrals", ["referred_id"])

    op.create_table(
        "commissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("referrer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referred_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("billing_period", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commissions_referrer_id", "commissions", ["referrer_id"])

    op.create_table(
        "payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("referrer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("fee_cents", sa.Integer(), nullable=False),
        sa.Column("stripe_transfer_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("commission_ids", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payouts_referrer_id", "payouts", ["referrer_id"])


def downgrade() -> None:
    op.drop_table("payouts")
    op.drop_table("commissions")
    op.drop_table("referrals")
    op.drop_table("referrer_profiles")
    op.drop_table("referral_codes")
