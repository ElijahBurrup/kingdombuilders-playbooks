"""Print the ad referral code for elijah@kingdombuilders.ai"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy import select
from api.database import async_session
from api.models.user import User
from api.models.referral import ReferralCode

async def run():
    async with async_session() as db:
        res = await db.execute(
            select(ReferralCode).join(User).where(User.email == "elijah@kingdombuilders.ai")
        )
        c = res.scalar_one_or_none()
        if c:
            print(f"CODE: {c.code}")
            print(f"LINK: https://kingdombuilders.ai/playbooks/?ref={c.code}")
        else:
            print("NOT FOUND")

if __name__ == "__main__":
    asyncio.run(run())
