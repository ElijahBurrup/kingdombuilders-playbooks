"""
New API payment endpoints for the FastAPI rebuild.

Handles authenticated Stripe checkout (individual playbooks + subscriptions),
customer portal sessions, and an expanded webhook that processes subscription
lifecycle events in addition to one-time purchases.
"""

import secrets
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models.purchase import Purchase, Subscription, StripeCustomer
from api.models.playbook import Playbook
from api.models.email import EmailLog
from api.schemas.purchase import CheckoutRequest, SubscriptionCheckoutRequest

router = APIRouter(prefix="/stripe", tags=["payments"])

# ---------------------------------------------------------------------------
# Stripe pricing lookup — maps plan_type to Stripe Price IDs.
# These should eventually live in the DB or env vars; hardcoded here for now.
# ---------------------------------------------------------------------------
SUBSCRIPTION_PRICES: dict[str, str] = {
    "monthly": settings.STRIPE_PRICE_MONTHLY or settings.STRIPE_PRICE_ID,
    "annual": settings.STRIPE_PRICE_YEARLY or settings.STRIPE_PRICE_ID,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_current_user_id(request: Request) -> str:
    """
    Extract and validate the current user from the request.
    Expects the auth middleware / dependency to have placed user info
    into request.state.  Returns the user_id as a string (UUID).
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return str(user.get("sub", ""))


async def _get_or_create_stripe_customer(
    user_id: str,
    email: str,
    db: AsyncSession,
) -> str:
    """Return existing Stripe customer ID or create a new one."""
    stripe.api_key = settings.STRIPE_SECRET_KEY

    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.user_id == user_id)
    )
    sc = result.scalar_one_or_none()
    if sc:
        return sc.stripe_customer_id

    customer = stripe.Customer.create(email=email, metadata={"user_id": user_id})
    new_sc = StripeCustomer(
        user_id=user_id,
        stripe_customer_id=customer.id,
    )
    db.add(new_sc)
    await db.commit()
    return customer.id


# ============================================================================
# GET /stripe/check-purchase — poll for purchase confirmation
# ============================================================================
@router.get("/check-purchase")
async def check_purchase(session_id: str, db: AsyncSession = Depends(get_db)):
    """Lightweight endpoint for the success page to poll until the webhook
    has created the Purchase record."""
    result = await db.execute(
        select(Purchase).where(Purchase.provider_session_id == session_id)
    )
    purchase = result.scalar_one_or_none()
    if purchase:
        return {"confirmed": True}
    return {"confirmed": False}


# ============================================================================
# POST /stripe/checkout — individual playbook purchase
# ============================================================================
@router.post("/checkout")
async def create_checkout(
    body: CheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user_id = await _get_current_user_id(request)

    # Look up the playbook
    result = await db.execute(
        select(Playbook).where(Playbook.slug == body.playbook_slug)
    )
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    # Check for duplicate purchase
    existing = await db.execute(
        select(Purchase).where(
            Purchase.user_id == user_id,
            Purchase.playbook_id == playbook.id,
            Purchase.status == "completed",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already own this playbook")

    try:
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
            cancel_url=f"{settings.BASE_URL}/{body.playbook_slug}?payment=cancelled",
            customer_creation="always",
            metadata={
                "product": "playbook",
                "playbook_slug": body.playbook_slug,
                "playbook_id": str(playbook.id),
                "user_id": user_id,
            },
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe checkout failed: {e}")


# ============================================================================
# POST /stripe/subscription — subscription checkout
# ============================================================================
@router.post("/subscription")
async def create_subscription_checkout(
    body: SubscriptionCheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user_id = await _get_current_user_id(request)

    price_id = SUBSCRIPTION_PRICES.get(body.plan_type)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Unknown plan type: {body.plan_type}")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.BASE_URL}/?payment=cancelled",
            customer_creation="always",
            metadata={
                "product": "subscription",
                "plan_type": body.plan_type,
                "user_id": user_id,
            },
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe subscription checkout failed: {e}")


# ============================================================================
# POST /stripe/portal — customer portal session
# ============================================================================
@router.post("/portal")
async def create_portal_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user_id = await _get_current_user_id(request)

    result = await db.execute(
        select(StripeCustomer).where(StripeCustomer.user_id == user_id)
    )
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="No Stripe customer found for this user")

    try:
        portal = stripe.billing_portal.Session.create(
            customer=sc.stripe_customer_id,
            return_url=f"{settings.BASE_URL}/",
        )
        return {"portal_url": portal.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe portal creation failed: {e}")


# ============================================================================
# POST /stripe/webhook — expanded webhook
# ============================================================================
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data_object, db)
    elif event_type == "customer.subscription.created":
        await _handle_subscription_event("created", data_object, db)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_event("updated", data_object, db)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_event("deleted", data_object, db)
    elif event_type == "invoice.paid":
        await _handle_invoice_paid(data_object, db)
    elif event_type == "invoice.payment_failed":
        await _handle_invoice_payment_failed(data_object, db)
    elif event_type == "charge.refunded":
        await _handle_charge_refunded(data_object, db)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Webhook sub-handlers
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

    # For subscription checkouts, the subscription.created event handles it


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
            return  # idempotent

        # Try to find user_id from metadata
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
