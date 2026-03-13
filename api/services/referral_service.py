"""
Referral service — business logic for the 3-level referral programme.

All functions accept an ``AsyncSession`` parameter so the caller controls
the database lifecycle.  A synchronous wrapper (``run_monthly_payouts_sync``)
is provided for APScheduler.
"""

import asyncio
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from uuid import UUID

import stripe
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import async_session as AsyncSessionLocal
from api.models.purchase import Subscription
from api.models.referral import (
    Commission,
    Payout,
    Referral,
    ReferralClaim,
    ReferralCode,
    ReferrerProfile,
)
from api.models.user import User

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# ---------------------------------------------------------------------------
# Commission rates (cents) per level, keyed by plan type
# ---------------------------------------------------------------------------
COMMISSION_RATES: dict[str, dict[int, int]] = {
    "single": {1: 50, 2: 50, 3: 50},
    "monthly": {1: 150, 2: 150, 3: 150},
    "yearly": {1: 125, 2: 125, 3: 125},
}

VELOCITY_LIMIT = 20  # max referrals per referrer within 24 hours
MAX_CODE_RETRIES = 10


# ============================================================================
# 1. Code generation
# ============================================================================
def generate_referral_code() -> str:
    """Return a 6-character uppercase alphanumeric code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


# ============================================================================
# 2. Ensure a user has a referral code
# ============================================================================
async def ensure_referral_code(
    user_id: UUID,
    db: AsyncSession,
) -> ReferralCode:
    """
    Return the existing ``ReferralCode`` for *user_id*, or create one.

    A retry loop handles the (unlikely) uniqueness collision on the
    generated code string.
    """
    result = await db.execute(
        select(ReferralCode).where(ReferralCode.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    for attempt in range(MAX_CODE_RETRIES):
        code = generate_referral_code()

        # Check for code collision
        collision = await db.execute(
            select(ReferralCode.id).where(ReferralCode.code == code)
        )
        if collision.scalar_one_or_none() is not None:
            logger.debug("Referral code collision on attempt %d: %s", attempt, code)
            continue

        referral_code = ReferralCode(user_id=user_id, code=code)
        db.add(referral_code)
        await db.flush()
        return referral_code

    raise RuntimeError(
        f"Failed to generate a unique referral code after {MAX_CODE_RETRIES} attempts"
    )


# ============================================================================
# 3. Process referral cookie (attribution)
# ============================================================================
async def process_referral_cookie(
    referred_user_id: UUID,
    referral_code: str,
    db: AsyncSession,
) -> None:
    """
    Attribute *referred_user_id* to the owner of *referral_code*.

    Creates up to 3 ``Referral`` rows (levels 1-3) by walking the
    referral chain upward.  Silently returns when:
    - the code does not exist
    - the code belongs to the referred user (self-referral)
    - the referred user already has referral records
    """
    # Look up code
    result = await db.execute(
        select(ReferralCode).where(ReferralCode.code == referral_code)
    )
    code_row = result.scalar_one_or_none()
    if code_row is None:
        logger.warning("Referral code not found: %s", referral_code)
        return

    referrer_id = code_row.user_id

    # Self-referral guard
    if referrer_id == referred_user_id:
        logger.info("Self-referral blocked for user %s", referred_user_id)
        return

    # Already-attributed guard
    existing = await db.execute(
        select(Referral.id).where(Referral.referred_id == referred_user_id).limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        return

    root_referrer_id = referrer_id

    # Level 1
    level1 = Referral(
        referrer_id=referrer_id,
        referred_id=referred_user_id,
        level=1,
        root_referrer_id=root_referrer_id,
    )
    db.add(level1)

    # Walk up: who referred code_owner? (level 1 referral where referred_id=referrer_id)
    l1_result = await db.execute(
        select(Referral).where(
            and_(Referral.referred_id == referrer_id, Referral.level == 1)
        )
    )
    l1_parent = l1_result.scalar_one_or_none()

    if l1_parent is not None:
        level2 = Referral(
            referrer_id=l1_parent.referrer_id,
            referred_id=referred_user_id,
            level=2,
            root_referrer_id=root_referrer_id,
        )
        db.add(level2)

        # Walk up again for level 3
        l2_result = await db.execute(
            select(Referral).where(
                and_(
                    Referral.referred_id == l1_parent.referrer_id,
                    Referral.level == 1,
                )
            )
        )
        l2_parent = l2_result.scalar_one_or_none()

        if l2_parent is not None:
            level3 = Referral(
                referrer_id=l2_parent.referrer_id,
                referred_id=referred_user_id,
                level=3,
                root_referrer_id=root_referrer_id,
            )
            db.add(level3)

    await db.flush()


# ============================================================================
# 4. Process commissions
# ============================================================================
async def process_commissions(
    referred_user_id: UUID,
    billing_period: str,
    db: AsyncSession,
    purchase_id: UUID | None = None,
    subscription_id: UUID | None = None,
    plan_type: str = "single",
) -> list[Commission]:
    """
    Create ``Commission`` rows for every referrer in the chain of
    *referred_user_id*.

    Idempotency: skips creation when a commission already exists for the
    same referrer + referred + billing_period combination.

    Returns a list of newly created ``Commission`` objects.
    """
    result = await db.execute(
        select(Referral).where(Referral.referred_id == referred_user_id)
    )
    referrals = result.scalars().all()

    if not referrals:
        return []

    rates = COMMISSION_RATES.get(plan_type, COMMISSION_RATES["single"])
    created: list[Commission] = []

    for ref in referrals:
        if ref.level not in rates:
            continue

        # Idempotency check
        existing = await db.execute(
            select(Commission.id).where(
                and_(
                    Commission.referrer_id == ref.referrer_id,
                    Commission.referred_id == referred_user_id,
                    Commission.billing_period == billing_period,
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue

        amount_cents = rates[ref.level]
        now = datetime.now(timezone.utc)

        commission = Commission(
            referrer_id=ref.referrer_id,
            referred_id=referred_user_id,
            purchase_id=purchase_id,
            subscription_id=subscription_id,
            level=ref.level,
            amount_cents=amount_cents,
            billing_period=billing_period,
            status="approved",
            approved_at=now,
        )
        db.add(commission)
        created.append(commission)

    if created:
        await db.flush()

    return created


# ============================================================================
# 5. Cancel pending commissions
# ============================================================================
async def cancel_pending_commissions(
    referred_user_id: UUID,
    db: AsyncSession,
) -> None:
    """
    Cancel all pending/approved commissions tied to *referred_user_id*
    for future billing periods (e.g. when a subscription is cancelled).
    """
    await db.execute(
        update(Commission)
        .where(
            and_(
                Commission.referred_id == referred_user_id,
                Commission.status.in_(["pending", "approved"]),
            )
        )
        .values(status="cancelled")
    )
    await db.flush()


# ============================================================================
# 6. Handle refund commissions
# ============================================================================
async def handle_refund_commissions(
    purchase_id: UUID | None,
    subscription_id: UUID | None,
    billing_period: str,
    db: AsyncSession,
) -> None:
    """
    Process commission adjustments when a payment is refunded.

    - Pending/approved commissions are cancelled outright.
    - Already-paid commissions are offset with a negative commission row.
    """
    # Build the base filter
    conditions = [Commission.billing_period == billing_period]
    if purchase_id is not None:
        conditions.append(Commission.purchase_id == purchase_id)
    elif subscription_id is not None:
        conditions.append(Commission.subscription_id == subscription_id)
    else:
        return

    result = await db.execute(
        select(Commission).where(and_(*conditions))
    )
    commissions = result.scalars().all()

    for comm in commissions:
        if comm.status in ("pending", "approved"):
            comm.status = "cancelled"
        elif comm.status == "paid":
            # Create an offsetting negative commission
            negative = Commission(
                referrer_id=comm.referrer_id,
                referred_id=comm.referred_id,
                purchase_id=comm.purchase_id,
                subscription_id=comm.subscription_id,
                level=comm.level,
                amount_cents=-comm.amount_cents,
                billing_period=f"{billing_period}-refund",
                status="approved",
                approved_at=datetime.now(timezone.utc),
            )
            db.add(negative)

    await db.flush()


# ============================================================================
# 7. Process monthly payouts
# ============================================================================
async def process_monthly_payouts(db: AsyncSession) -> dict:
    """
    Aggregate approved commissions per referrer, issue Stripe transfers
    for those above the minimum threshold, and record ``Payout`` rows.

    Returns a summary dict with counts and totals.
    """
    min_payout = settings.REFERRAL_MIN_PAYOUT_CENTS
    tax_threshold = settings.REFERRAL_TAX_THRESHOLD_CENTS

    # Aggregate approved commissions by referrer
    agg_query = (
        select(
            Commission.referrer_id,
            func.sum(Commission.amount_cents).label("total_cents"),
            func.array_agg(Commission.id).label("commission_ids"),
        )
        .where(Commission.status == "approved")
        .group_by(Commission.referrer_id)
        .having(func.sum(Commission.amount_cents) >= min_payout)
    )
    result = await db.execute(agg_query)
    rows = result.all()

    summary: dict = {
        "processed": 0,
        "skipped": 0,
        "total_paid_cents": 0,
        "errors": [],
        "tax_warnings": [],
    }

    for row in rows:
        referrer_id = row.referrer_id
        total_cents = int(row.total_cents)
        commission_ids = row.commission_ids

        # Fetch referrer profile
        profile_result = await db.execute(
            select(ReferrerProfile).where(ReferrerProfile.user_id == referrer_id)
        )
        profile = profile_result.scalar_one_or_none()

        # Skip if no profile, payouts paused, or Stripe Connect not ready
        if profile is None:
            summary["skipped"] += 1
            logger.info("No referrer profile for user %s, skipping payout", referrer_id)
            continue

        if profile.payouts_paused:
            summary["skipped"] += 1
            logger.info("Payouts paused for user %s, skipping", referrer_id)
            continue

        if not profile.stripe_connect_id or profile.connect_status != "active":
            summary["skipped"] += 1
            logger.info(
                "Stripe Connect not ready for user %s (id=%s, status=%s), skipping",
                referrer_id,
                profile.stripe_connect_id,
                profile.connect_status,
            )
            continue

        # Calculate fee: $0.25 flat + 0.25% of total
        fee_cents = 25 + round(total_cents * 0.0025)
        transfer_amount = total_cents - fee_cents

        if transfer_amount <= 0:
            summary["skipped"] += 1
            continue

        # Issue Stripe transfer
        now = datetime.now(timezone.utc)
        try:
            transfer = stripe.Transfer.create(
                amount=transfer_amount,
                currency="usd",
                destination=profile.stripe_connect_id,
                description=f"Referral payout for {now.strftime('%Y-%m')}",
            )
            stripe_transfer_id = transfer.id
        except stripe.error.StripeError as exc:
            logger.error("Stripe transfer failed for user %s: %s", referrer_id, exc)
            summary["errors"].append(
                {"referrer_id": str(referrer_id), "error": str(exc)}
            )
            continue

        # Create payout record
        payout = Payout(
            referrer_id=referrer_id,
            amount_cents=transfer_amount,
            fee_cents=fee_cents,
            stripe_transfer_id=stripe_transfer_id,
            status="completed",
            commission_ids=[str(cid) for cid in commission_ids],
            completed_at=now,
        )
        db.add(payout)

        # Mark commissions as paid
        await db.execute(
            update(Commission)
            .where(Commission.id.in_(commission_ids))
            .values(status="paid", paid_at=now)
        )

        # Update lifetime earnings
        profile.lifetime_earnings_cents += total_cents
        profile.updated_at = now

        summary["processed"] += 1
        summary["total_paid_cents"] += transfer_amount

        # Tax threshold check
        if profile.lifetime_earnings_cents >= tax_threshold and not profile.tax_info_required:
            profile.tax_info_required = True
            summary["tax_warnings"].append(str(referrer_id))
            logger.info(
                "User %s exceeded $%.2f tax threshold (lifetime: $%.2f)",
                referrer_id,
                tax_threshold / 100,
                profile.lifetime_earnings_cents / 100,
            )

    await db.commit()

    logger.info(
        "Monthly payouts complete: %d processed, %d skipped, $%.2f paid",
        summary["processed"],
        summary["skipped"],
        summary["total_paid_cents"] / 100,
    )
    return summary


# ============================================================================
# 8. Get referral stats
# ============================================================================
async def get_referral_stats(user_id: UUID, db: AsyncSession) -> dict:
    """
    Return a summary dict with the user's referral code, link,
    counts, and earnings.
    """
    # Ensure the user has a code
    code_row = await ensure_referral_code(user_id, db)

    # Total level-1 referrals
    total_result = await db.execute(
        select(func.count()).where(
            and_(Referral.referrer_id == user_id, Referral.level == 1)
        )
    )
    total_referrals = total_result.scalar() or 0

    # Active subscribers among referred users (level 1)
    active_result = await db.execute(
        select(func.count(func.distinct(Subscription.user_id)))
        .select_from(Referral)
        .join(Subscription, Subscription.user_id == Referral.referred_id)
        .where(
            and_(
                Referral.referrer_id == user_id,
                Referral.level == 1,
                Subscription.status == "active",
            )
        )
    )
    active_subscribers = active_result.scalar() or 0

    # Current balance (approved commissions)
    balance_result = await db.execute(
        select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
            and_(
                Commission.referrer_id == user_id,
                Commission.status == "approved",
            )
        )
    )
    current_balance_cents = int(balance_result.scalar())

    # Lifetime earnings from profile, or fall back to sum of paid + approved
    profile_result = await db.execute(
        select(ReferrerProfile).where(ReferrerProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    if profile and profile.lifetime_earnings_cents > 0:
        lifetime_earnings_cents = profile.lifetime_earnings_cents
    else:
        lifetime_result = await db.execute(
            select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
                and_(
                    Commission.referrer_id == user_id,
                    Commission.status.in_(["paid", "approved"]),
                )
            )
        )
        lifetime_earnings_cents = int(lifetime_result.scalar())

    base_url = settings.BASE_URL.rstrip("/")
    referral_link = f"{base_url}/?ref={code_row.code}"

    return {
        "referral_code": code_row.code,
        "referral_link": referral_link,
        "total_referrals": total_referrals,
        "active_subscribers": active_subscribers,
        "current_balance_cents": current_balance_cents,
        "lifetime_earnings_cents": lifetime_earnings_cents,
    }


# ============================================================================
# 9. Get referral tree
# ============================================================================
async def get_referral_tree(user_id: UUID, db: AsyncSession) -> dict:
    """
    Return a tree structure showing level-1 detail and level-2/3 summaries.
    """
    # Level 1 — detailed
    l1_result = await db.execute(
        select(Referral, User)
        .join(User, User.id == Referral.referred_id)
        .where(and_(Referral.referrer_id == user_id, Referral.level == 1))
        .order_by(Referral.created_at.desc())
    )
    l1_rows = l1_result.all()

    level_1_detail = []
    for ref, user in l1_rows:
        # Mask email: first 2 chars + ***@domain
        email = user.email
        at_idx = email.index("@")
        masked_email = email[:2] + "***" + email[at_idx:]

        # Check subscription status
        sub_result = await db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == ref.referred_id,
                    Subscription.status == "active",
                )
            )
            .limit(1)
        )
        active_sub = sub_result.scalar_one_or_none()

        # Calculate monthly commission for this referral
        commission_result = await db.execute(
            select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
                and_(
                    Commission.referrer_id == user_id,
                    Commission.referred_id == ref.referred_id,
                    Commission.status.in_(["approved", "paid"]),
                )
            )
        )
        total_commission_cents = int(commission_result.scalar())

        level_1_detail.append({
            "referred_id": str(ref.referred_id),
            "display_name": user.display_name or masked_email,
            "email_masked": masked_email,
            "signed_up_at": ref.created_at.isoformat() if ref.created_at else None,
            "has_active_subscription": active_sub is not None,
            "plan_type": active_sub.plan_type if active_sub else None,
            "total_commission_cents": total_commission_cents,
        })

    # Level 2 — count and total only
    l2_count_result = await db.execute(
        select(func.count()).where(
            and_(Referral.referrer_id == user_id, Referral.level == 2)
        )
    )
    l2_count = l2_count_result.scalar() or 0

    l2_earnings_result = await db.execute(
        select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
            and_(
                Commission.referrer_id == user_id,
                Commission.level == 2,
                Commission.status.in_(["approved", "paid"]),
            )
        )
    )
    l2_earnings = int(l2_earnings_result.scalar())

    # Level 3 — count and total only
    l3_count_result = await db.execute(
        select(func.count()).where(
            and_(Referral.referrer_id == user_id, Referral.level == 3)
        )
    )
    l3_count = l3_count_result.scalar() or 0

    l3_earnings_result = await db.execute(
        select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
            and_(
                Commission.referrer_id == user_id,
                Commission.level == 3,
                Commission.status.in_(["approved", "paid"]),
            )
        )
    )
    l3_earnings = int(l3_earnings_result.scalar())

    return {
        "level_1": {
            "count": len(level_1_detail),
            "referrals": level_1_detail,
        },
        "level_2": {
            "count": l2_count,
            "total_earnings_cents": l2_earnings,
        },
        "level_3": {
            "count": l3_count,
            "total_earnings_cents": l3_earnings,
        },
    }


# ============================================================================
# 10. Get earnings breakdown
# ============================================================================
async def get_earnings_breakdown(user_id: UUID, db: AsyncSession) -> dict:
    """
    Return a month-by-month earnings breakdown for the last 12 months,
    plus current balance and lifetime total.
    """
    # Monthly breakdown via billing_period grouping
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)

    monthly_result = await db.execute(
        select(
            Commission.billing_period,
            func.sum(Commission.amount_cents).label("total_cents"),
            func.count().label("commission_count"),
        )
        .where(
            and_(
                Commission.referrer_id == user_id,
                Commission.status.in_(["approved", "paid"]),
                Commission.created_at >= twelve_months_ago,
            )
        )
        .group_by(Commission.billing_period)
        .order_by(Commission.billing_period.desc())
    )
    monthly_rows = monthly_result.all()

    months = []
    for row in monthly_rows:
        months.append({
            "billing_period": row.billing_period,
            "total_cents": int(row.total_cents),
            "commission_count": row.commission_count,
        })

    # Current balance
    balance_result = await db.execute(
        select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
            and_(
                Commission.referrer_id == user_id,
                Commission.status == "approved",
            )
        )
    )
    current_balance_cents = int(balance_result.scalar())

    # Lifetime total
    lifetime_result = await db.execute(
        select(func.coalesce(func.sum(Commission.amount_cents), 0)).where(
            and_(
                Commission.referrer_id == user_id,
                Commission.status.in_(["paid", "approved"]),
            )
        )
    )
    lifetime_total_cents = int(lifetime_result.scalar())

    return {
        "months": months,
        "current_balance_cents": current_balance_cents,
        "lifetime_total_cents": lifetime_total_cents,
    }


# ============================================================================
# 11. Velocity limit check
# ============================================================================
async def check_velocity_limit(referrer_id: UUID, db: AsyncSession) -> bool:
    """
    Return ``True`` if *referrer_id* has exceeded the 24-hour referral
    velocity limit (more than 20 referrals in the last 24 hours).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(func.count()).where(
            and_(
                Referral.referrer_id == referrer_id,
                Referral.created_at > cutoff,
            )
        )
    )
    count = result.scalar() or 0
    return count > VELOCITY_LIMIT


# ============================================================================
# 12. Sync wrapper for APScheduler
# ============================================================================
def run_monthly_payouts_sync() -> dict:
    """
    Synchronous entry point for APScheduler.

    Creates a fresh async session, runs the payout logic, and returns
    the summary dict.
    """

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            return await process_monthly_payouts(db)

    return asyncio.run(_run())


# ============================================================================
# 13. Check if user has referral attribution
# ============================================================================
async def has_referral_attribution(user_id: UUID, db: AsyncSession) -> bool:
    """Return True if *user_id* already has at least one Referral record as the referred party."""
    result = await db.execute(
        select(Referral.id).where(Referral.referred_id == user_id).limit(1)
    )
    return result.scalar_one_or_none() is not None


# ============================================================================
# 14. Create a referral claim
# ============================================================================
async def create_referral_claim(
    claimant_id: UUID,
    referral_code: str,
    db: AsyncSession,
) -> ReferralClaim:
    """
    Create a pending claim for *claimant_id* to be attributed to the owner
    of *referral_code*.  Sends a confirmation email to the referrer.

    Raises ValueError with a user-friendly message on any guard failure.
    """
    # Guard: claimant must not already be attributed
    if await has_referral_attribution(claimant_id, db):
        raise ValueError("You already have a referral attribution and cannot submit a claim.")

    # Guard: no existing pending claim for this claimant
    existing = await db.execute(
        select(ReferralClaim).where(
            and_(
                ReferralClaim.claimant_id == claimant_id,
                ReferralClaim.status == "pending",
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("You already have a pending referral claim. Please wait for it to be confirmed or expire.")

    # Look up code
    code_result = await db.execute(
        select(ReferralCode).where(ReferralCode.code == referral_code.upper().strip())
    )
    code_row = code_result.scalar_one_or_none()
    if code_row is None:
        raise ValueError("Referral code not found. Please check the code and try again.")

    referrer_id = code_row.user_id

    # Self-referral guard
    if referrer_id == claimant_id:
        raise ValueError("You cannot claim your own referral code.")

    # Generate a secure token
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    claim = ReferralClaim(
        claimant_id=claimant_id,
        referrer_id=referrer_id,
        token=token,
        status="pending",
        expires_at=expires_at,
    )
    db.add(claim)
    await db.flush()

    # Send email to referrer
    from api.services.email_service import send_referral_claim_request_email

    referrer_result = await db.execute(
        select(User).where(User.id == referrer_id)
    )
    referrer = referrer_result.scalar_one()

    claimant_result = await db.execute(
        select(User).where(User.id == claimant_id)
    )
    claimant = claimant_result.scalar_one()

    claimant_name = claimant.display_name or claimant.email.split("@")[0]
    # Mask email: first 2 chars + ***@domain
    email = claimant.email
    at_idx = email.index("@")
    masked = email[:2] + "***" + email[at_idx:]

    base = settings.BASE_URL.rstrip("/")
    prefix = settings.URL_PREFIX
    confirm_url = f"{base}{prefix}/referrals/confirm-claim?token={token}"

    send_referral_claim_request_email(
        referrer_email=referrer.email,
        claimant_display_name=claimant_name,
        claimant_email_masked=masked,
        confirm_url=confirm_url,
    )

    await db.commit()
    return claim


# ============================================================================
# 15. Confirm a referral claim (via token from email)
# ============================================================================
async def confirm_referral_claim(token: str, db: AsyncSession) -> str:
    """
    Confirm a pending referral claim identified by *token*.
    Backfills the referral chain and notifies the claimant.

    Returns a status message string.
    """
    result = await db.execute(
        select(ReferralClaim).where(ReferralClaim.token == token)
    )
    claim = result.scalar_one_or_none()

    if claim is None:
        return "invalid"

    if claim.status != "pending":
        return "already_processed"

    now = datetime.now(timezone.utc)
    if claim.expires_at < now:
        claim.status = "expired"
        await db.commit()
        return "expired"

    # Guard: claimant must still not have attribution (race condition check)
    if await has_referral_attribution(claim.claimant_id, db):
        claim.status = "cancelled"
        await db.commit()
        return "already_attributed"

    # Backfill the referral chain using process_referral_cookie logic
    await _backfill_referral_chain(claim.claimant_id, claim.referrer_id, db)

    claim.status = "confirmed"
    claim.confirmed_at = now
    await db.flush()

    # Send confirmation to claimant
    from api.services.email_service import send_referral_claim_confirmed_email

    claimant_result = await db.execute(
        select(User).where(User.id == claim.claimant_id)
    )
    claimant = claimant_result.scalar_one()

    referrer_result = await db.execute(
        select(User).where(User.id == claim.referrer_id)
    )
    referrer = referrer_result.scalar_one()

    referrer_name = referrer.display_name or referrer.email.split("@")[0]
    send_referral_claim_confirmed_email(
        claimant_email=claimant.email,
        referrer_display_name=referrer_name,
    )

    await db.commit()
    return "confirmed"


async def _backfill_referral_chain(
    referred_id: UUID,
    referrer_id: UUID,
    db: AsyncSession,
) -> None:
    """
    Create Referral rows for all 3 levels, same logic as process_referral_cookie
    but takes a referrer_id directly instead of a code string.
    """
    root_referrer_id = referrer_id

    # Level 1
    level1 = Referral(
        referrer_id=referrer_id,
        referred_id=referred_id,
        level=1,
        root_referrer_id=root_referrer_id,
    )
    db.add(level1)

    # Walk up: who referred the referrer?
    l1_result = await db.execute(
        select(Referral).where(
            and_(Referral.referred_id == referrer_id, Referral.level == 1)
        )
    )
    l1_parent = l1_result.scalar_one_or_none()

    if l1_parent is not None:
        level2 = Referral(
            referrer_id=l1_parent.referrer_id,
            referred_id=referred_id,
            level=2,
            root_referrer_id=root_referrer_id,
        )
        db.add(level2)

        # Walk up again for level 3
        l2_result = await db.execute(
            select(Referral).where(
                and_(
                    Referral.referred_id == l1_parent.referrer_id,
                    Referral.level == 1,
                )
            )
        )
        l2_parent = l2_result.scalar_one_or_none()

        if l2_parent is not None:
            level3 = Referral(
                referrer_id=l2_parent.referrer_id,
                referred_id=referred_id,
                level=3,
                root_referrer_id=root_referrer_id,
            )
            db.add(level3)

    await db.flush()
