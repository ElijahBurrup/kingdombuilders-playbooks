from pydantic import BaseModel, ConfigDict


class ReferralStatsResponse(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    active_subscribers: int
    current_balance_cents: int
    lifetime_earnings_cents: int

    model_config = ConfigDict(from_attributes=True)


class ReferralTreeLevel1(BaseModel):
    display_name: str
    masked_email: str
    signup_date: str
    subscription_status: str
    monthly_commission_cents: int


class ReferralTreeResponse(BaseModel):
    level_1: list[ReferralTreeLevel1]
    level_2_count: int
    level_2_total_commission_cents: int
    level_3_count: int
    level_3_total_commission_cents: int


class EarningsMonth(BaseModel):
    month: str
    amount_cents: int


class EarningsResponse(BaseModel):
    monthly_breakdown: list[EarningsMonth]
    current_balance_cents: int
    next_payout_estimate_cents: int
    lifetime_total_cents: int


class PayoutItem(BaseModel):
    date: str
    amount_cents: int
    fee_cents: int
    status: str
    stripe_transfer_id: str | None

    model_config = ConfigDict(from_attributes=True)


class PayoutListResponse(BaseModel):
    payouts: list[PayoutItem]


class ConnectResponse(BaseModel):
    onboarding_url: str
