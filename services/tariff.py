"""Tariff plan logic for Nazoratchi bot.

Plans:
  FREE  — basic moderation, 1 group, NUVI ads daily, 10 banned words
  PRO   — no ads, 3 groups, full features, 100 banned words
  VIP   — everything unlimited, 10 groups, auto-kick, real-time stats
"""
from datetime import datetime, timezone

# Plan limits
PLAN_LIMITS = {
    "free": {
        "max_groups": 1,
        "max_banned_words": 10,
        "flood_control": False,
        "night_mode": False,
        "welcome_message": False,
        "warn_customizable": False,
        "auto_kick": False,
        "stats": False,
        "ads_enabled": True,       # NUVI sends ads to group
        "branding": True,          # "Powered by NUVI"
        "price": 0,
    },
    "pro": {
        "max_groups": 3,
        "max_banned_words": 100,
        "flood_control": True,
        "night_mode": True,
        "welcome_message": True,
        "warn_customizable": True,
        "auto_kick": False,
        "stats": True,
        "ads_enabled": False,
        "branding": False,
        "price": 49_000,
    },
    "vip": {
        "max_groups": 10,
        "max_banned_words": 999_999,  # unlimited
        "flood_control": True,
        "night_mode": True,
        "welcome_message": True,
        "warn_customizable": True,
        "auto_kick": True,
        "stats": True,
        "ads_enabled": False,
        "branding": False,
        "price": 149_000,
    },
}


def get_plan_limits(plan: str) -> dict:
    """Get limits for a plan."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def is_plan_active(plan: str, expires_at) -> bool:
    """Check if a paid plan is still active."""
    if plan == "free":
        return True
    if expires_at is None:
        return False
    if isinstance(expires_at, datetime):
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > now
    return False


def get_effective_plan(plan: str, expires_at) -> str:
    """Get effective plan — falls back to free if expired."""
    if is_plan_active(plan, expires_at):
        return plan
    return "free"


def can_use_feature(plan: str, expires_at, feature: str) -> bool:
    """Check if a feature is available for this plan."""
    effective = get_effective_plan(plan, expires_at)
    limits = get_plan_limits(effective)
    return limits.get(feature, False)


def plan_display_name(plan: str) -> str:
    names = {
        "free": "🆓 Free",
        "pro": "⭐ Pro",
        "vip": "💎 VIP",
    }
    return names.get(plan, "🆓 Free")


def plan_price_text(plan: str) -> str:
    prices = {
        "free": "Bepul",
        "pro": "49,000 so'm/oy",
        "vip": "149,000 so'm/oy",
    }
    return prices.get(plan, "Bepul")
