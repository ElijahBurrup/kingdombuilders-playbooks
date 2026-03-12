"""
Generate referral codes for all existing users who don't have one.
Run after the referral tables migration.

Usage:
    python -m api.scripts.seed_referral_codes
"""

import asyncio

from sqlalchemy import select

from api.database import AsyncSessionLocal
from api.models.user import User
from api.models.referral import ReferralCode
from api.services.referral_service import ensure_referral_code


async def seed():
    async with AsyncSessionLocal() as db:
        # Find users without referral codes
        result = await db.execute(
            select(User.id).where(
                ~User.id.in_(select(ReferralCode.user_id))
            )
        )
        user_ids = result.scalars().all()

        print(f"Found {len(user_ids)} users without referral codes.")

        for uid in user_ids:
            code = await ensure_referral_code(uid, db)
            print(f"  Created code {code.code} for user {uid}")

        print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
