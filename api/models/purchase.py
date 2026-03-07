import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class StripeCustomer(Base):
    __tablename__ = "stripe_customers"

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
    stripe_customer_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "playbook_id", "payment_provider",
            name="uq_purchase_user_playbook_provider",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    playbook_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=True,
    )
    payment_provider: Mapped[str] = mapped_column(nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(nullable=True)
    provider_session_id: Mapped[str | None] = mapped_column(nullable=True)
    amount_cents: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(
        default="usd", server_default=text("'usd'")
    )
    status: Mapped[str] = mapped_column(
        default="completed", server_default=text("'completed'")
    )
    download_token: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    downloads_remaining: Mapped[int | None] = mapped_column(
        default=5, server_default=text("5"), nullable=True
    )
    download_expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMPTZ, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
    playbook: Mapped["Playbook"] = relationship()


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_type: Mapped[str] = mapped_column(nullable=False)
    price_cents: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(
        default="usd", server_default=text("'usd'")
    )
    payment_provider: Mapped[str] = mapped_column(nullable=False)
    provider_subscription_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        default="active", server_default=text("'active'")
    )
    current_period_start: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()


class GooglePlayToken(Base):
    __tablename__ = "google_play_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_token: Mapped[str] = mapped_column(Text, nullable=False)
    product_id: Mapped[str] = mapped_column(nullable=False)
    order_id: Mapped[str | None] = mapped_column(nullable=True)
    purchase_type: Mapped[str] = mapped_column(nullable=False)
    acknowledged: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()
