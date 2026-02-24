import secrets
from datetime import datetime, timedelta, timezone

import stripe
from flask import redirect, request

import config
from database import (
    get_purchase_by_session_id,
    create_purchase,
)

stripe.api_key = config.STRIPE_SECRET_KEY


def create_checkout_session():
    """Create a Stripe Checkout Session and redirect to Stripe."""
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price": config.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url=f"{config.BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{config.BASE_URL}/conductorsplaybook?payment=cancelled",
            customer_creation="always",
            metadata={"product": "conductors_playbook"},
        )
        return redirect(session.url, code=303)
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return redirect(f"{config.BASE_URL}/conductorsplaybook?payment=error")


def handle_webhook():
    """Process Stripe webhook events."""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_successful_purchase(session)

    return "OK", 200


def _handle_successful_purchase(session):
    """Record purchase, generate download token, send delivery email."""
    session_id = session["id"]

    # Idempotency: skip if already processed
    if get_purchase_by_session_id(session_id):
        return

    customer_email = session["customer_details"]["email"]
    download_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    create_purchase(
        stripe_session_id=session_id,
        customer_email=customer_email,
        download_token=download_token,
        downloads_remaining=5,
        expires_at=expires_at,
        stripe_payment_intent=session.get("payment_intent"),
        amount_cents=session.get("amount_total", 6700),
    )

    # Send delivery email
    from emails import send_delivery_email
    send_delivery_email(customer_email, download_token)

    # Schedule follow-up emails
    from scheduler import schedule_followup_emails
    schedule_followup_emails(customer_email, download_token)
