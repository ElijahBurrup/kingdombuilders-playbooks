import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id", name="uq_referral_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    root_referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    referrer: Mapped["User"] = relationship(foreign_keys=[referrer_id])
    referred: Mapped["User"] = relationship(foreign_keys=[referred_id])


class Commission(Base):
    __tablename__ = "commissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchases.id", ondelete="SET NULL"),
        nullable=True,
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_period: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        default="pending", server_default=text("'pending'")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)

    referrer: Mapped["User"] = relationship(foreign_keys=[referrer_id])
    referred: Mapped["User"] = relationship(foreign_keys=[referred_id])


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_transfer_id: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        default="pending", server_default=text("'pending'")
    )
    commission_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)

    referrer: Mapped["User"] = relationship()


class ReferrerProfile(Base):
    __tablename__ = "referrer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    stripe_connect_id: Mapped[str | None] = mapped_column(nullable=True)
    connect_status: Mapped[str] = mapped_column(
        default="pending", server_default=text("'pending'")
    )
    tax_info_required: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    tax_info_collected: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    lifetime_earnings_cents: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )
    payouts_paused: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
