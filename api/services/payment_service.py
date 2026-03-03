"""
Payment service — business logic for Stripe checkout, subscriptions,
and webhook processing.

This module is used by the new API payment router (api/routers/payments.py)
and can also be called from other services.
"""

import secrets
from datetime import datetime, timedelta, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.models.playbook import Playbook
from api.models.purchase import Purchase, Subscription, StripeCustomer

# ---------------------------------------------------------------------------
# Ensure Stripe is configured
# ---------------------------------------------------------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY

# Subscription price IDs — should eventually be env vars or DB-driven
SUBSCRIPTION_PRICES: dict[str, str] = {
    "monthly": settings.STRIPE_PRICE_ID,
    "annual": settings.STRIPE_PRICE_ID,
}


# ============================================================================
# Checkout creation
# ============================================================================
async def create_stripe_checkout(
    playbook_slug: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    """
    Create a Stripe Checkout Session for an individual playbook purchase.

    Returns dict with ``checkout_url`` and ``session_id``.
    Raises ValueError if the playbook is not found or already owned.
    """
    result = await db.execute(
        select(Playbook).where(Playbook.slug == playbook_slug)
    )
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise ValueError(f"Playbook not found: {playbook_slug}")

    # Check for duplicate purchase
    existing = await db.execute(
        select(Purchase).where(
            Purchase.user_id == user_id,
            Purchase.playbook_id == playbook.id,
            Purchase.status == "completed",
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("You already own this playbook")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": playbook.title},
                "unit_amount": playbook.price_cents,
            },
            "quantity": 1,
        }],
        success_url=f"{settings.BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.BASE_URL}/{playbook_slug}?payment=cancelled",
        customer_creation="always",
        metadata={
            "product": "playbook",
            "playbook_slug": playbook_slug,
            "playbook_id": str(playbook.id),
            "user_id": user_id,
        },
    )

    return {"checkout_url": session.url, "session_id": session.id}


async def create_subscription_checkout(
    plan_type: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    """
    Create a Stripe Checkout Session for a subscription.

    Returns dict with ``checkout_url`` and ``session_id``.
    Raises ValueError if the plan type is unknown.
    """
    price_id = SUBSCRIPTION_PRICES.get(plan_type)
    if not price_id:
        raise ValueError(f"Unknown plan type: {plan_type}")

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.BASE_URL}/?payment=cancelled",
        customer_creation="always",
        metadata={
            "product": "subscription",
            "plan_type": plan_type,
            "user_id": user_id,
        },
    )

    return {"checkout_url": session.url, "session_id": session.id}


# ============================================================================
# Webhook processing
# ============================================================================
async def handle_stripe_webhook(
    payload: bytes,
    sig_header: str,
    db: AsyncSession,
) -> dict:
    """
    Verify and dispatch a Stripe webhook event.

    Returns a dict with ``status`` key.  Raises ValueError on
    verification failure.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise ValueError("Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid signature")

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data_object, db)
    elif event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        sub_event = event_type.rsplit(".", 1)[-1]  # "created" / "updated" / "deleted"
        await _handle_subscription_event(sub_event, data_object, db)
    elif event_type == "invoice.paid":
        await _handle_invoice_paid(data_object, db)
    elif event_type == "invoice.payment_failed":
        await _handle_invoice_payment_failed(data_object, db)
    elif event_type == "charge.refunded":
        await _handle_charge_refunded(data_object, db)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Internal handlers
# ---------------------------------------------------------------------------
async def _handle_checkout_completed(session: dict, db: AsyncSession) -> None:
    """Record a one-time playbook purchase from a completed checkout session."""
    metadata = session.get("metadata", {})
    product = metadata.get("product", "")
    user_id = metadata.get("user_id")
    session_id = session["id"]

    # Idempotency
    existing = await db.execute(
        select(Purchase).where(Purchase.provider_session_id == session_id)
    )
    if existing.scalar_one_or_none():
        return

    if product == "playbook":
        playbook_id = metadata.get("playbook_id")
        if not playbook_id or not user_id:
            return

        customer_email = session.get("customer_details", {}).get("email", "")
        download_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        purchase = Purchase(
            user_id=user_id,
            playbook_id=playbook_id,
            payment_provider="stripe",
            provider_payment_id=session.get("payment_intent"),
            provider_session_id=session_id,
            amount_cents=session.get("amount_total", 0),
            status="completed",
            download_token=download_token,
            downloads_remaining=5,
            download_expires_at=expires_at,
        )
        db.add(purchase)
        await db.commit()

        # Send delivery email and schedule follow-ups
        from api.services.email_service import send_delivery_email
        from api.services.scheduler_service import schedule_followup_emails

        send_delivery_email(customer_email, download_token)
        schedule_followup_emails(customer_email, download_token)


async def _handle_subscription_event(
    event_type: str,
    subscription_obj: dict,
    db: AsyncSession,
) -> None:
    """Handle subscription create / update / delete events."""
    provider_sub_id = subscription_obj["id"]

    result = await db.execute(
        select(Subscription).where(
            Subscription.provider_subscription_id == provider_sub_id
        )
    )
    existing_sub = result.scalar_one_or_none()

    if event_type == "created":
        if existing_sub:
            return

        metadata = subscription_obj.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_type = metadata.get("plan_type", "monthly")

        if not user_id:
            print(f"Subscription {provider_sub_id} created without user_id in metadata")
            return

        current_period_start = datetime.fromtimestamp(
            subscription_obj["current_period_start"], tz=timezone.utc
        )
        current_period_end = datetime.fromtimestamp(
            subscription_obj["current_period_end"], tz=timezone.utc
        )

        price_cents = 0
        items = subscription_obj.get("items", {}).get("data", [])
        if items:
            price_cents = items[0].get("price", {}).get("unit_amount", 0)

        new_sub = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            price_cents=price_cents,
            payment_provider="stripe",
            provider_subscription_id=provider_sub_id,
            status=subscription_obj.get("status", "active"),
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=subscription_obj.get("cancel_at_period_end", False),
        )
        db.add(new_sub)
        await db.commit()

    elif event_type == "updated":
        if not existing_sub:
            return

        existing_sub.status = subscription_obj.get("status", existing_sub.status)
        existing_sub.cancel_at_period_end = subscription_obj.get(
            "cancel_at_period_end", existing_sub.cancel_at_period_end
        )
        existing_sub.current_period_start = datetime.fromtimestamp(
            subscription_obj["current_period_start"], tz=timezone.utc
        )
        existing_sub.current_period_end = datetime.fromtimestamp(
            subscription_obj["current_period_end"], tz=timezone.utc
        )
        existing_sub.updated_at = datetime.now(timezone.utc)
        await db.commit()

    elif event_type == "deleted":
        if not existing_sub:
            return

        existing_sub.status = "canceled"
        existing_sub.updated_at = datetime.now(timezone.utc)
        await db.commit()


async def _handle_invoice_paid(invoice: dict, db: AsyncSession) -> None:
    """Update subscription period when a recurring invoice is paid."""
    sub_id = invoice.get("subscription")
    if not sub_id:
        return

    result = await db.execute(
        select(Subscription).where(
            Subscription.provider_subscription_id == sub_id
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    lines = invoice.get("lines", {}).get("data", [])
    if lines:
        period = lines[0].get("period", {})
        if period.get("start"):
            sub.current_period_start = datetime.fromtimestamp(
                period["start"], tz=timezone.utc
            )
        if period.get("end"):
            sub.current_period_end = datetime.fromtimestamp(
                period["end"], tz=timezone.utc
            )

    sub.status = "active"
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def _handle_invoice_payment_failed(invoice: dict, db: AsyncSession) -> None:
    """Mark subscription as past_due on payment failure."""
    sub_id = invoice.get("subscription")
    if not sub_id:
        return

    result = await db.execute(
        select(Subscription).where(
            Subscription.provider_subscription_id == sub_id
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    sub.status = "past_due"
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def _handle_charge_refunded(charge: dict, db: AsyncSession) -> None:
    """Mark a purchase as refunded when a charge.refunded event fires."""
    payment_intent_id = charge.get("payment_intent")
    if not payment_intent_id:
        return

    result = await db.execute(
        select(Purchase).where(
            Purchase.provider_payment_id == payment_intent_id
        )
    )
    purchase = result.scalar_one_or_none()
    if not purchase:
        return

    purchase.status = "refunded"
    purchase.updated_at = datetime.now(timezone.utc)
    await db.commit()
