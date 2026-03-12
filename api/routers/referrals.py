"""
Referral system endpoints.

Handles referral stats, tree visualization, earnings breakdown,
payout history, and Stripe Connect onboarding for referrers.
"""

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.dependencies import get_current_user
from api.models.referral import Payout, ReferrerProfile
from api.models.user import User
from api.schemas.referral import (
    ConnectResponse,
    EarningsResponse,
    PayoutItem,
    PayoutListResponse,
    ReferralStatsResponse,
    ReferralTreeResponse,
)
from api.services.referral_service import (
    ensure_referral_code,
    get_earnings_breakdown,
    get_referral_stats,
    get_referral_tree,
)

router = APIRouter(prefix="/referrals", tags=["referrals"])


# ============================================================================
# GET /referrals/me — referral stats for the current user
# ============================================================================
@router.get("/me", response_model=ReferralStatsResponse)
async def get_my_referral_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferralStatsResponse:
    """Return the current user's referral code, link, and high-level stats."""
    await ensure_referral_code(current_user, db)
    return await get_referral_stats(current_user, db)


# ============================================================================
# GET /referrals/tree — referral tree breakdown
# ============================================================================
@router.get("/tree", response_model=ReferralTreeResponse)
async def get_my_referral_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferralTreeResponse:
    """Return the current user's referral tree with level details."""
    return await get_referral_tree(current_user, db)


# ============================================================================
# GET /referrals/earnings — earnings breakdown
# ============================================================================
@router.get("/earnings", response_model=EarningsResponse)
async def get_my_earnings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EarningsResponse:
    """Return monthly earnings breakdown and balance summary."""
    return await get_earnings_breakdown(current_user, db)


# ============================================================================
# GET /referrals/payouts — payout history
# ============================================================================
@router.get("/payouts", response_model=PayoutListResponse)
async def get_my_payouts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PayoutListResponse:
    """Return the current user's payout history."""
    result = await db.execute(
        select(Payout)
        .where(Payout.referrer_id == current_user.id)
        .order_by(Payout.created_at.desc())
    )
    payouts = result.scalars().all()

    return PayoutListResponse(
        payouts=[
            PayoutItem(
                date=p.created_at.isoformat(),
                amount_cents=p.amount_cents,
                fee_cents=p.fee_cents,
                status=p.status,
                stripe_transfer_id=p.stripe_transfer_id,
            )
            for p in payouts
        ]
    )


# ============================================================================
# POST /referrals/connect — initiate Stripe Connect onboarding
# ============================================================================
@router.post("/connect", response_model=ConnectResponse)
async def create_connect_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectResponse:
    """Create a Stripe Express connected account and return the onboarding URL."""
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Check if user already has a connected account
    result = await db.execute(
        select(ReferrerProfile).where(ReferrerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile and profile.stripe_connect_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stripe Connect account already exists. Use /connect/refresh to continue onboarding.",
        )

    try:
        account = stripe.Account.create(
            type="express",
            country="US",
            email=current_user.email,
            capabilities={"transfers": {"requested": True}},
        )

        link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{settings.BASE_URL}{settings.URL_PREFIX}/referrals?connect=refresh",
            return_url=f"{settings.BASE_URL}{settings.URL_PREFIX}/referrals?connect=success",
            type="account_onboarding",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe Connect error: {e}",
        )

    if profile:
        profile.stripe_connect_id = account.id
        profile.connect_status = "onboarding"
    else:
        profile = ReferrerProfile(
            user_id=current_user.id,
            stripe_connect_id=account.id,
            connect_status="onboarding",
        )
        db.add(profile)

    await db.commit()

    return ConnectResponse(onboarding_url=link.url)


# ============================================================================
# GET /referrals/connect/refresh — refresh Stripe Connect onboarding link
# ============================================================================
@router.get("/connect/refresh", response_model=ConnectResponse)
async def refresh_connect_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectResponse:
    """Generate a fresh onboarding link for an existing Stripe Connect account."""
    stripe.api_key = settings.STRIPE_SECRET_KEY

    result = await db.execute(
        select(ReferrerProfile).where(ReferrerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile or not profile.stripe_connect_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Stripe Connect account found. Use POST /connect to create one.",
        )

    try:
        link = stripe.AccountLink.create(
            account=profile.stripe_connect_id,
            refresh_url=f"{settings.BASE_URL}{settings.URL_PREFIX}/referrals?connect=refresh",
            return_url=f"{settings.BASE_URL}{settings.URL_PREFIX}/referrals?connect=success",
            type="account_onboarding",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe Connect error: {e}",
        )

    return ConnectResponse(onboarding_url=link.url)
