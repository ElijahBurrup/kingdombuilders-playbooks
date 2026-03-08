import secrets
from datetime import datetime, timedelta, timezone

import stripe
from flask import redirect, request, jsonify

import config
from database import (
    get_purchase_by_session_id,
    create_purchase,
    grant_playbook_access,
    create_subscription,
    update_subscription_status,
)

stripe.api_key = config.STRIPE_SECRET_KEY

# Free playbook slugs (no payment required)
FREE_SLUGS = {
    "conductors-playbook",
    "the-squirrel-economy",
    "the-salmon-journey",
    "the-wolfs-table",
    "the-crows-gambit",
}


def create_checkout_session():
    """Create a Stripe Checkout Session for single playbook, monthly, or yearly."""
    data = request.form or request.get_json(silent=True) or {}
    mode = data.get("mode", "single")  # single | monthly | yearly
    slug = data.get("slug", "")

    # Pick the right price ID and Stripe mode
    if mode == "monthly":
        price_id = config.STRIPE_PRICE_MONTHLY
        stripe_mode = "subscription"
        metadata = {"mode": "monthly"}
    elif mode == "yearly":
        price_id = config.STRIPE_PRICE_YEARLY
        stripe_mode = "subscription"
        metadata = {"mode": "yearly"}
    else:
        price_id = config.STRIPE_PRICE_SINGLE
        stripe_mode = "payment"
        metadata = {"mode": "single", "slug": slug}

    if not price_id:
        return jsonify({"error": "Stripe price not configured"}), 500

    cancel_path = f"/{slug.replace('-', '')}" if slug else "/"
    try:
        session_params = {
            "mode": stripe_mode,
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": f"{config.BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{config.BASE_URL}{cancel_path}?payment=cancelled",
            "customer_creation": "always" if stripe_mode == "payment" else None,
            "metadata": metadata,
        }
        # Remove None values
        session_params = {k: v for k, v in session_params.items() if v is not None}

        session = stripe.checkout.Session.create(**session_params)
        return redirect(session.url, code=303)
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return redirect(f"{config.BASE_URL}{cancel_path}?payment=error")


def handle_webhook():
    """Process Stripe webhook events."""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    if not config.STRIPE_WEBHOOK_SECRET:
        return "Webhook secret not configured", 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(obj)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(obj)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(obj)

    return "OK", 200


def _handle_checkout_completed(session):
    """Handle successful checkout — grant access based on mode."""
    session_id = session["id"]

    # Idempotency
    if get_purchase_by_session_id(session_id):
        return

    customer_email = session.get("customer_details", {}).get("email", "")
    metadata = session.get("metadata", {})
    mode = metadata.get("mode", "single")
    amount_cents = session.get("amount_total", 0)

    # Record purchase
    download_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=365)

    create_purchase(
        stripe_session_id=session_id,
        customer_email=customer_email,
        download_token=download_token,
        downloads_remaining=99,
        expires_at=expires_at,
        stripe_payment_intent=session.get("payment_intent"),
        amount_cents=amount_cents,
    )

    if mode == "single":
        # Grant access to specific playbook
        slug = metadata.get("slug", "")
        if slug:
            grant_playbook_access(customer_email, slug, "single", session_id)
    elif mode in ("monthly", "yearly"):
        # Subscription — record subscription and grant all access
        stripe_sub_id = session.get("subscription")
        stripe_customer_id = session.get("customer")
        if stripe_sub_id:
            create_subscription(
                customer_email=customer_email,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_sub_id,
                plan=mode,
                status="active",
            )

    # Send delivery email
    try:
        from emails import send_delivery_email
        send_delivery_email(customer_email, download_token)
    except Exception as e:
        print(f"Delivery email failed: {e}")


def _handle_subscription_updated(subscription):
    """Handle subscription status changes (renewal, payment failure, etc.)."""
    status = subscription.get("status", "")
    stripe_sub_id = subscription.get("id", "")
    period_end = subscription.get("current_period_end")

    period_end_str = None
    if period_end:
        period_end_str = datetime.fromtimestamp(period_end, tz=timezone.utc).isoformat()

    # Map Stripe statuses to our statuses
    if status in ("active", "trialing"):
        db_status = "active"
    elif status == "past_due":
        db_status = "past_due"
    else:
        db_status = "canceled"

    update_subscription_status(stripe_sub_id, db_status, period_end_str)


def _handle_subscription_deleted(subscription):
    """Handle subscription cancellation."""
    stripe_sub_id = subscription.get("id", "")
    update_subscription_status(stripe_sub_id, "canceled")
