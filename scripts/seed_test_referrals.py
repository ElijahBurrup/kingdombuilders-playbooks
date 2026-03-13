"""
Seed test referral data for elijah@kingdombuilders.ai.

Creates 79 total referrals across 3 levels, monthly commissions
for the past 6 months, and 4 completed payouts.

Usage:
    python -m scripts.seed_test_referrals
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from api.database import async_session
from api.models.user import User
from api.models.referral import (
    Commission,
    Payout,
    Referral,
    ReferralCode,
    ReferrerProfile,
)
from api.models.purchase import Subscription
from api.services.referral_service import ensure_referral_code

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ADMIN_EMAIL = "elijah@kingdombuilders.ai"
NOW = datetime.now(timezone.utc)

# Distribution: 15 L1, 35 L2, 29 L3 = 79 total
L1_COUNT = 15
L2_COUNT = 35
L3_COUNT = 29

# Fake user name pools
FIRST_NAMES = [
    "James", "Sarah", "Michael", "Emma", "David", "Olivia", "Daniel", "Sophia",
    "Matthew", "Isabella", "Andrew", "Mia", "Joshua", "Charlotte", "Ethan",
    "Amelia", "Nathan", "Harper", "Ryan", "Abigail", "Tyler", "Emily",
    "Brandon", "Ella", "Kevin", "Grace", "Marcus", "Lily", "Aaron", "Chloe",
    "Jacob", "Zoe", "Noah", "Aria", "Logan", "Riley", "Luke", "Nora",
    "Owen", "Layla", "Caleb", "Scarlett", "Isaac", "Hannah", "Levi", "Stella",
    "Samuel", "Violet", "Eli", "Aurora", "Henry", "Savannah", "Jack", "Audrey",
    "Alexander", "Brooklyn", "Sebastian", "Bella", "Carter", "Claire",
    "Wyatt", "Skylar", "Jayden", "Lucy", "Gabriel", "Paisley", "Julian",
    "Everly", "Liam", "Anna", "Mason", "Caroline", "Lincoln", "Genesis",
    "Asher", "Naomi", "Theodore", "Elena", "Jaxon",
]

LAST_NAMES = [
    "Parker", "Chen", "Williams", "Johnson", "Rodriguez", "Kim", "Davis",
    "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White",
    "Harris", "Martin", "Thompson", "Garcia", "Clark", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Hill", "Green",
    "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Roberts",
    "Turner", "Phillips", "Campbell", "Evans", "Edwards", "Collins",
    "Stewart", "Morris", "Reed", "Cook", "Morgan", "Bell", "Murphy",
    "Rivera", "Cooper", "Richardson", "Cox", "Howard", "Ward", "Torres",
    "Peterson", "Gray", "Ramirez", "James", "Watson", "Brooks", "Kelly",
    "Sanders", "Price", "Bennett", "Wood", "Barnes", "Ross", "Henderson",
    "Coleman", "Jenkins", "Perry", "Powell", "Long", "Patterson", "Hughes",
    "Butler",
]


def fake_email(first: str, last: str, idx: int) -> str:
    return f"test.{first.lower()}.{last.lower()}.{idx}@example.com"


async def seed():
    async with async_session() as db:
        # Find admin user
        result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        admin = result.scalar_one_or_none()
        if not admin:
            print(f"ERROR: {ADMIN_EMAIL} not found.")
            return

        admin_id = admin.id
        print(f"Admin: {admin.email} ({admin_id})")

        # Ensure admin has a referral code
        await ensure_referral_code(admin_id, db)

        # Clean previous test data
        await db.execute(text(
            "DELETE FROM commissions WHERE referrer_id = :uid OR referred_id IN "
            "(SELECT id FROM users WHERE email LIKE 'test.%@example.com')"
        ), {"uid": str(admin_id)})
        await db.execute(text("DELETE FROM payouts WHERE referrer_id = :uid"), {"uid": str(admin_id)})
        await db.execute(text(
            "DELETE FROM referrals WHERE referrer_id = :uid OR referred_id IN "
            "(SELECT id FROM users WHERE email LIKE 'test.%@example.com')"
        ), {"uid": str(admin_id)})
        await db.execute(text("DELETE FROM users WHERE email LIKE 'test.%@example.com'"))
        await db.flush()
        print("Cleaned previous test data.")

        # --- Create fake users ---
        all_users = []
        total_needed = L1_COUNT + L2_COUNT + L3_COUNT  # 79
        for i in range(total_needed):
            first = FIRST_NAMES[i % len(FIRST_NAMES)]
            last = LAST_NAMES[i % len(LAST_NAMES)]
            email = fake_email(first, last, i)
            user = User(
                email=email,
                display_name=f"{first} {last}",
                role="user",
                email_verified=True,
                is_active=True,
            )
            db.add(user)
            all_users.append(user)

        await db.flush()
        print(f"Created {len(all_users)} test users.")

        # Split users into levels
        l1_users = all_users[:L1_COUNT]
        l2_users = all_users[L1_COUNT:L1_COUNT + L2_COUNT]
        l3_users = all_users[L1_COUNT + L2_COUNT:]

        # --- Create referral codes for L1 users (they refer L2) ---
        for u in l1_users:
            await ensure_referral_code(u.id, db)
        await db.flush()

        # --- Create referral records ---

        # Level 1: admin referred all L1 users
        for i, u in enumerate(l1_users):
            days_ago = 180 - (i * 10)  # staggered over ~5 months
            ref = Referral(
                referrer_id=admin_id,
                referred_id=u.id,
                level=1,
                root_referrer_id=admin_id,
                created_at=NOW - timedelta(days=max(days_ago, 10)),
            )
            db.add(ref)

        # Level 2: L1 users referred L2 users (distribute evenly)
        # The referral table tracks (referrer, referred) pairs.
        # For admin's view: admin->L1 at level 1, admin->L2 at level 2, admin->L3 at level 3
        # For each L2 user, L1_user is their direct referrer (level 1 from L1's perspective)
        l2_idx = 0
        for i, l1_user in enumerate(l1_users):
            share = L2_COUNT // L1_COUNT + (1 if i < L2_COUNT % L1_COUNT else 0)
            for j in range(share):
                if l2_idx >= len(l2_users):
                    break
                l2_user = l2_users[l2_idx]
                days_ago = 150 - (l2_idx * 3)
                ts = NOW - timedelta(days=max(days_ago, 5))

                # L1 user -> L2 user (L1 user's direct referral)
                db.add(Referral(
                    referrer_id=l1_user.id,
                    referred_id=l2_user.id,
                    level=1,
                    root_referrer_id=admin_id,
                    created_at=ts,
                ))
                # Admin -> L2 user at level 2 (admin is 2 hops away)
                db.add(Referral(
                    referrer_id=admin_id,
                    referred_id=l2_user.id,
                    level=2,
                    root_referrer_id=admin_id,
                    created_at=ts,
                ))
                l2_idx += 1

        # Level 3: some L2 users referred L3 users
        l3_idx = 0
        for i, l2_user in enumerate(l2_users):
            if l3_idx >= len(l3_users):
                break
            if i % 2 != 0:
                continue
            l3_user = l3_users[l3_idx]
            days_ago = 90 - (l3_idx * 2)
            ts = NOW - timedelta(days=max(days_ago, 3))

            # L2 user -> L3 user (L2 user's direct referral)
            db.add(Referral(
                referrer_id=l2_user.id,
                referred_id=l3_user.id,
                level=1,
                root_referrer_id=admin_id,
                created_at=ts,
            ))
            # Find which L1 user referred this L2 user, they get level 2
            l1_parent_idx = 0
            count = 0
            for k, l1u in enumerate(l1_users):
                share = L2_COUNT // L1_COUNT + (1 if k < L2_COUNT % L1_COUNT else 0)
                if count + share > i:
                    l1_parent_idx = k
                    break
                count += share
            db.add(Referral(
                referrer_id=l1_users[l1_parent_idx].id,
                referred_id=l3_user.id,
                level=2,
                root_referrer_id=admin_id,
                created_at=ts,
            ))
            # Admin -> L3 user at level 3
            db.add(Referral(
                referrer_id=admin_id,
                referred_id=l3_user.id,
                level=3,
                root_referrer_id=admin_id,
                created_at=ts,
            ))
            l3_idx += 1

        await db.flush()
        print(f"Created referrals: {L1_COUNT} L1, {L2_COUNT} L2, {l3_idx} L3")

        # --- Create subscriptions for referred users (most are active monthly) ---
        active_count = 0
        for u in all_users:
            # 70% have active subscriptions
            if hash(str(u.id)) % 10 < 7:
                sub = Subscription(
                    user_id=u.id,
                    provider_subscription_id=f"sub_test_{str(u.id)[:8]}",
                    payment_provider="stripe",
                    plan_type="monthly",
                    status="active",
                    price_cents=1000,
                    current_period_start=NOW - timedelta(days=28),
                    current_period_end=NOW + timedelta(days=2),
                )
                db.add(sub)
                active_count += 1
        await db.flush()
        print(f"Created {active_count} active subscriptions.")

        # --- Create commissions for the past 6 months ---
        months = []
        for m in range(6):
            month_start = NOW - timedelta(days=30 * (5 - m))
            period = month_start.strftime("%Y-%m")
            months.append((period, month_start))

        commission_count = 0
        for period, month_date in months:
            # L1 commissions: $1.50 each
            for u in l1_users:
                # Not all referrals earn every month (simulate churn)
                if hash(f"{u.id}{period}") % 10 < 8:
                    db.add(Commission(
                        referrer_id=admin_id,
                        referred_id=u.id,
                        level=1,
                        amount_cents=150,
                        billing_period=period,
                        status="paid" if month_date < NOW - timedelta(days=30) else "approved",
                        created_at=month_date,
                        approved_at=month_date,
                        paid_at=month_date + timedelta(days=15) if month_date < NOW - timedelta(days=30) else None,
                    ))
                    commission_count += 1

            # L2 commissions: $1.50 each
            for u in l2_users:
                if hash(f"{u.id}{period}") % 10 < 7:
                    db.add(Commission(
                        referrer_id=admin_id,
                        referred_id=u.id,
                        level=2,
                        amount_cents=150,
                        billing_period=period,
                        status="paid" if month_date < NOW - timedelta(days=30) else "approved",
                        created_at=month_date,
                        approved_at=month_date,
                        paid_at=month_date + timedelta(days=15) if month_date < NOW - timedelta(days=30) else None,
                    ))
                    commission_count += 1

            # L3 commissions: $1.50 each
            for u in l3_users[:l3_idx]:
                if hash(f"{u.id}{period}") % 10 < 6:
                    db.add(Commission(
                        referrer_id=admin_id,
                        referred_id=u.id,
                        level=3,
                        amount_cents=150,
                        billing_period=period,
                        status="paid" if month_date < NOW - timedelta(days=30) else "approved",
                        created_at=month_date,
                        approved_at=month_date,
                        paid_at=month_date + timedelta(days=15) if month_date < NOW - timedelta(days=30) else None,
                    ))
                    commission_count += 1

        await db.flush()
        print(f"Created {commission_count} commissions across 6 months.")

        # --- Create referrer profile ---
        result = await db.execute(
            select(ReferrerProfile).where(ReferrerProfile.user_id == admin_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = ReferrerProfile(
                user_id=admin_id,
                stripe_connect_id="acct_test_demo123",
                connect_status="active",
                lifetime_earnings_cents=0,
            )
            db.add(profile)
            await db.flush()

        # --- Create 4 monthly payouts ---
        total_paid = 0
        for m in range(4):
            month_start = NOW - timedelta(days=30 * (4 - m))
            period = month_start.strftime("%Y-%m")

            # Calculate this month's paid commissions
            # ~12 L1 + ~24 L2 + ~17 L3 active per month = ~53 × $1.50 = ~$79.50
            payout_amount = 7500 + (m * 800)  # increasing each month
            fee = 25 + round(payout_amount * 0.0025)
            net = payout_amount - fee

            payout = Payout(
                referrer_id=admin_id,
                amount_cents=net,
                fee_cents=fee,
                stripe_transfer_id=f"tr_test_{period.replace('-', '')}_{m}",
                status="completed",
                commission_ids=[],
                created_at=month_start + timedelta(days=15),
                completed_at=month_start + timedelta(days=15),
            )
            db.add(payout)
            total_paid += net

        # Update lifetime earnings
        profile.lifetime_earnings_cents = total_paid
        await db.flush()

        await db.commit()

        print(f"\nDone! Summary:")
        print(f"  79 total referrals (15 L1, 35 L2, 29 L3)")
        print(f"  {active_count} active subscribers")
        print(f"  {commission_count} commissions over 6 months")
        print(f"  4 completed payouts, lifetime: ${total_paid / 100:.2f}")
        print(f"  Referrer profile: Stripe Connect active")


if __name__ == "__main__":
    asyncio.run(seed())
