"""
Grant a user full playbook access by creating a lifetime subscription.

Usage:
    python -m scripts.grant_user_access <email>

Creates a comped "yearly" subscription with a far-future end date so the user
has full access to all paid playbooks without going through Stripe.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from api.database import async_session
from api.models.purchase import Subscription
from api.models.user import User


async def grant(email: str):
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"ERROR: User not found: {email}")
            sys.exit(1)

        # Check if they already have an active subscription
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.status == "active",
            )
        )
        existing = sub_result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        far_future = now + timedelta(days=3650)  # 10 years

        if existing:
            # Extend the existing subscription
            existing.current_period_end = far_future
            existing.status = "active"
            existing.cancel_at_period_end = False
            print(f"Extended existing subscription for {email} until {far_future.date()}")
        else:
            sub = Subscription(
                user_id=user.id,
                plan_type="yearly",
                price_cents=0,
                payment_provider="comp",
                provider_subscription_id=f"comp_{user.id}_{int(now.timestamp())}",
                status="active",
                current_period_start=now,
                current_period_end=far_future,
                cancel_at_period_end=False,
            )
            db.add(sub)
            print(f"Created comped subscription for {email} until {far_future.date()}")

        await db.commit()
        print(f"SUCCESS: {email} now has full playbook access.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.grant_user_access <email>")
        sys.exit(1)
    asyncio.run(grant(sys.argv[1]))
