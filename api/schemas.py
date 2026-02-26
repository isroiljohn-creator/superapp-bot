"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel
from typing import Optional, List


# ── User ─────────────────────────────────
class UserProfile(BaseModel):
    telegram_id: int
    name: Optional[str] = None
    age: Optional[int] = None
    goal_tag: Optional[str] = None
    level_tag: Optional[str] = None
    lead_score: int = 0
    lead_segment: str = "content_only"
    subscription_status: str = "inactive"
    registered_at: Optional[str] = None


# ── Referral ─────────────────────────────
class ReferralStats(BaseModel):
    referral_link: str
    total_invited: int = 0
    valid_referrals: int = 0
    paid_referrals: int = 0
    balance: int = 0
    club_price: int = 97_000
    amount_for_free: int = 0  # how much more needed for free sub


# ── Payment ──────────────────────────────
class PaymentInitRequest(BaseModel):
    provider: str = "click"  # click | payme


class PaymentInitResponse(BaseModel):
    payment_id: int
    base_price: int
    referral_discount: int
    final_price: int
    payment_url: str


# ── Course ───────────────────────────────
class CourseModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    order: int
    is_locked: bool = False
    completion_pct: float = 0.0
    is_completed: bool = False


class CourseProgressRequest(BaseModel):
    module_id: int
    watch_time: int = 0      # seconds
    completion_pct: float = 0.0


# ── Webhook ──────────────────────────────
class ClickWebhookData(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    amount: float
    action: int
    error: int
    error_note: str
    sign_time: str
    sign_string: str


class PaymeWebhookData(BaseModel):
    method: str
    params: dict
