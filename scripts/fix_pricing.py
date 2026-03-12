"""
One-time script to fix pricing_type on all playbooks.
Sets everything to paid, then marks the 8 free slugs as free.

Usage:
    python -m scripts.fix_pricing
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from api.database import async_session

FREE_SLUGS = (
    "conductors-playbook",
    "lay-it-down",
    "the-mockingbirds-song",
    "the-lifted-ceiling",
    "the-tide-pools-echo",
    "dad-talks-the-dopamine-drought",
    "the-mantis-shrimps-eye",
    "the-hermit-crabs-shell",
)


async def run():
    async with async_session() as db:
        r1 = await db.execute(
            text("UPDATE playbooks SET pricing_type='paid', price_cents=250 WHERE pricing_type='free'")
        )
        print(f"Set {r1.rowcount} playbooks to paid.")

        placeholders = ", ".join(f"'{s}'" for s in FREE_SLUGS)
        r2 = await db.execute(
            text(f"UPDATE playbooks SET pricing_type='free', price_cents=0 WHERE slug IN ({placeholders})")
        )
        print(f"Set {r2.rowcount} playbooks to free.")

        await db.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(run())
