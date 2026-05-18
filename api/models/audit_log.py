"""Audit log for sign-up / checkout / webhook / email pipeline events.

Every step that affects whether a paying customer gets access — auth/register,
auth/login, auth/google, /create-checkout-session, every Stripe webhook
handler branch, every email send — records an audit_log row.

When a customer says "I paid but the site doesn't recognize me," we look up
their email here, see the exact sequence of events, find the gap, and fix.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base, TIMESTAMPTZ


class AuditLog(Base):
    """A single observable event in the sign-up / pay / access pipeline.

    event_type is a short slug like:
      - "auth.register"
      - "auth.login"
      - "auth.google"
      - "checkout.created"
      - "webhook.received"
      - "webhook.checkout_completed"
      - "webhook.subscription_created"
      - "webhook.subscription_updated"
      - "webhook.invoice_paid"
      - "webhook.no_user_id"           (silent-bail case)
      - "webhook.no_stripe_customer"   (silent-bail case)
      - "webhook.handler_error"
      - "email.delivery_sent"
      - "email.delivery_failed"
      - "admin.reconcile_user"

    status is "success", "warning", "error" — surfaces severity at a glance
    so the admin viewer can red-flag the row.

    email is denormalized (not a FK to users) because some events occur
    BEFORE a user record exists (e.g., checkout failed on register).
    Anything we know about the actor at the moment of the event gets
    stamped here.
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_email_timestamp", "email", "timestamp"),
        Index("ix_audit_log_event_type_timestamp", "event_type", "timestamp"),
        Index("ix_audit_log_user_id", "user_id"),
        Index("ix_audit_log_session_id", "provider_session_id"),
        Index("ix_audit_log_subscription_id", "provider_subscription_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ,
        server_default=text("now()"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")

    # Best-effort actor identity at the moment of the event. Email is the
    # most reliable handle because it survives across auth + Stripe + email
    # send. user_id is set when known. Both are nullable.
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Provider references for cross-system reconciliation.
    provider_session_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    provider_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    provider_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Free-form description of what happened. Read by humans, not parsed.
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured extras for debugging. event_type-specific shape.
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    # Request context (helps detect bot/fraud and reconstruct user journey).
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    user: Mapped[Optional["User"]] = relationship()
