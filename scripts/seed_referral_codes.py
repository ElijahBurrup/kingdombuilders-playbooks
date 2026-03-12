"""
Seed script — generates referral codes for all existing users who don't have one.
Run after the referral tables migration.

Usage:
    python -m scripts.seed_referral_codes
"""

import asyncio
import sys
from pathlib import Path

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from api.database import async_session
from api.models.user import User
from api.models.referral import ReferralCode
from api.services.referral_service import ensure_referral_code


async def seed():
    async with async_session() as db:
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

        await db.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(seed())
