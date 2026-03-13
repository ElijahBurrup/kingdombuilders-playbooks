"""
Ensure elijah@kingdombuilders.ai has a referral code for embedding in ads.
Prints the code so it can be used in ad campaign links.

Usage:
    python -m scripts.seed_ad_referral
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from api.database import async_session
from api.models.user import User
from api.models.referral import ReferralCode
from api.services.referral_service import ensure_referral_code


async def seed():
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.email == "elijah@kingdombuilders.ai")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("ERROR: User elijah@kingdombuilders.ai not found in database.")
            print("This user must exist before running this script.")
            return

        code = await ensure_referral_code(user.id, db)
        await db.commit()

        print(f"Ad referral code for elijah@kingdombuilders.ai: {code.code}")
        print(f"Ad link: https://kingdombuilders.ai/playbooks/?ref={code.code}")
        print()
        print("Embed this link in all ad campaigns. Users who register through")
        print("this link will be attributed to the admin account, blocking")
        print("retroactive referral claims.")


if __name__ == "__main__":
    asyncio.run(seed())
