from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.playbook import Playbook
from api.models.purchase import Purchase, Subscription


async def check_access(
    user_id: UUID, playbook: Playbook, db: AsyncSession
) -> bool:
    """
    Determine whether a user has access to read a playbook's full content.

    Access is granted if any of the following are true:
    1. The playbook is free (pricing_type == 'free').
    2. The user has an active subscription (status='active' and
       current_period_end is in the future).
    3. The user has a completed individual purchase for this playbook
       (status='completed').
    """
    # 1. Free playbooks are accessible to everyone
    if playbook.pricing_type == "free":
        return True

    # 2. Check for an active subscription
    now = datetime.now(timezone.utc)
    sub_result = await db.execute(
        select(Subscription.id).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Subscription.current_period_end > now,
        ).limit(1)
    )
    if sub_result.scalar_one_or_none() is not None:
        return True

    # 3. Check for a completed individual purchase
    purchase_result = await db.execute(
        select(Purchase.id).where(
            Purchase.user_id == user_id,
            Purchase.playbook_id == playbook.id,
            Purchase.status == "completed",
        ).limit(1)
    )
    if purchase_result.scalar_one_or_none() is not None:
        return True

    return False
