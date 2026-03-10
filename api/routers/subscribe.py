"""
Subscriber management router.

Handles JSON-based email subscription (lead magnet signups)
and unsubscribe via token.
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models.email import Subscriber
from api.schemas.email import SubscribeRequest, SubscribeResponse

router = APIRouter(prefix="/subscribe", tags=["subscribe"])


# ============================================================================
# POST /subscribe — JSON endpoint (new API)
# ============================================================================
@router.post("", response_model=SubscribeResponse)
async def subscribe(
    body: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new subscriber and send the lead magnet email.
    Idempotent: if the email already exists, we still send the lead magnet
    (they might not have received it the first time).
    """
    email = body.email.strip().lower()

    # Upsert — insert or do nothing on conflict
    stmt = (
        pg_insert(Subscriber)
        .values(email=email, source=body.source)
        .on_conflict_do_nothing(index_elements=["email"])
    )
    await db.execute(stmt)
    await db.commit()

    # Send lead magnet email
    from api.services.email_service import send_lead_magnet_email

    try:
        send_lead_magnet_email(email)
    except Exception as e:
        print(f"Lead magnet email failed for {email}: {e}")

    # Schedule nurture drip sequence (emails 2-5)
    from api.services.scheduler_service import schedule_nurture_sequence

    try:
        schedule_nurture_sequence(email)
    except Exception as e:
        print(f"Nurture schedule failed for {email}: {e}")

    return SubscribeResponse(
        message="Thanks for subscribing! Check your email for your free chapter."
    )


# ============================================================================
# POST /subscribe/unsubscribe — unsubscribe via token
# ============================================================================
@router.post("/unsubscribe")
async def unsubscribe(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a subscriber as unsubscribed using a token.

    The token is a SHA-256 hash of the subscriber's email, providing a
    simple verification mechanism without requiring authentication.
    """
    # Find a subscriber whose email hashes to this token
    result = await db.execute(select(Subscriber).where(Subscriber.unsubscribed == False))
    subscribers = result.scalars().all()

    matched_subscriber = None
    for sub in subscribers:
        email_hash = hashlib.sha256(sub.email.encode()).hexdigest()
        if email_hash == token:
            matched_subscriber = sub
            break

    if not matched_subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unsubscribe token not found or already unsubscribed.",
        )

    matched_subscriber.unsubscribed = True
    await db.commit()

    return {"message": "You have been successfully unsubscribed."}
