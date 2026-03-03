import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    source: Mapped[str] = mapped_column(
        default="salmon-journey-ch1",
        server_default=text("'salmon-journey-ch1'"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    unsubscribed: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User | None"] = relationship()


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_email: Mapped[str] = mapped_column(nullable=False)
    email_type: Mapped[str] = mapped_column(nullable=False)
    template_name: Mapped[str | None] = mapped_column(nullable=True)
    resend_id: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        default="sent", server_default=text("'sent'")
    )
    sent_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User | None"] = relationship()


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

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
    email_type: Mapped[str] = mapped_column(nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False)
    sent: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    canceled: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    context_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    user: Mapped["User"] = relationship()


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(unique=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(nullable=False)
    discount_value: Mapped[int] = mapped_column(nullable=False)
    playbook_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playbooks.id", ondelete="SET NULL"),
        nullable=True,
    )
    max_uses: Mapped[int | None] = mapped_column(nullable=True)
    current_uses: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    valid_from: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=text("now()")
    )

    playbook: Mapped["Playbook | None"] = relationship()
