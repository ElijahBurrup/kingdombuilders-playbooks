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
    referred_id: str
    display_name: str
    email: str
    signup_date: str | None
    status: str
    monthly_commission_cents: int


class ReferralTreeSummary(BaseModel):
    count: int
    total_commission_cents: int


class ReferralTreeResponse(BaseModel):
    level_1: list[ReferralTreeLevel1]
    level_1_commission_cents: int
    level_2_summary: ReferralTreeSummary
    level_3_summary: ReferralTreeSummary


class EarningsMonth(BaseModel):
    month: str
    amount_cents: int
    label: str


class EarningsResponse(BaseModel):
    monthly: list[EarningsMonth]
    balance_cents: int
    lifetime_cents: int


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
