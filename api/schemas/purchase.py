from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    playbook_slug: str
    promo_code: str | None = None


class SubscriptionCheckoutRequest(BaseModel):
    plan_type: Literal["monthly", "annual"]


class PurchaseResponse(BaseModel):
    id: UUID
    playbook_slug: str
    amount_cents: int
    status: str
    download_token: str | None
    created_at: datetime


class SubscriptionResponse(BaseModel):
    id: UUID
    plan_type: str
    status: str
    current_period_end: datetime
    cancel_at_period_end: bool
