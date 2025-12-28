"""
Core Entitlements System
Manages plan-based access control and usage limits for YASHA.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional, Literal
from core.db import db
import pytz

# Uzbekistan timezone
UZ_TZ = pytz.timezone('Asia/Tashkent')

# Plan definitions
# Plan Constraints
PLAN_FREE = "free"
PLAN_PLUS = "plus"
PLAN_PRO = "pro"

PlanType = Literal['free', 'plus', 'pro']
FeatureKey = Literal['menu_generate', 'workout_generate', 'calorie_scan', 'ai_chat', 'meal_swap', 'coach_strict_mode']
PeriodType = Literal['day', 'month']

# Feature limits by plan
PLAN_LIMITS: Dict[PlanType, Dict[FeatureKey, Dict[str, any]]] = {
    PLAN_FREE: {
        'menu_generate': {'limit': 0, 'period': 'month'},      # No custom menu
        'workout_generate': {'limit': 0, 'period': 'month'},   # No custom workout
        'calorie_scan': {'limit': 0, 'period': 'day'},         # No scan
        'ai_chat': {'limit': 0, 'period': 'day'},             # No AI chat
        'meal_swap': {'limit': 0, 'period': 'day'},            # No swaps
        'coach_strict_mode': {'limit': 0, 'period': 'month'},  # No strict mode
    },
    PLAN_PLUS: {
        'menu_generate': {'limit': 1, 'period': 'month'},      # 7-day plan basically implies generating new plan
        'workout_generate': {'limit': 1, 'period': 'month'},
        'calorie_scan': {'limit': 2, 'period': 'day'},         # 2 times per day
        'ai_chat': {'limit': 5, 'period': 'day'},             # Moderate chat
        'meal_swap': {'limit': 2, 'period': 'day'},            # 1-2 swaps/day
        'coach_strict_mode': {'limit': 0, 'period': 'month'},  # No strict mode
    },
    PLAN_PRO: {
        'menu_generate': {'limit': None, 'period': 'month'},   # Unlimited
        'workout_generate': {'limit': None, 'period': 'month'},
        'calorie_scan': {'limit': None, 'period': 'day'},
        'ai_chat': {'limit': None, 'period': 'day'},
        'meal_swap': {'limit': None, 'period': 'day'},
        'coach_strict_mode': {'limit': None, 'period': 'month'}, # Yes
    }
}

def get_period_start(period_type: PeriodType) -> date:
    """Get period start date for current period in Uzbekistan timezone."""
    now = datetime.now(UZ_TZ)
    if period_type == 'day':
        return now.date()
    elif period_type == 'month':
        return now.replace(day=1).date()
    else:
        raise ValueError(f"Invalid period_type: {period_type}")

def get_reset_datetime(period_type: PeriodType) -> datetime:
    """Get next reset datetime in Uzbekistan timezone."""
    now = datetime.now(UZ_TZ)
    if period_type == 'day':
        # Next day at midnight
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period_type == 'month':
        # First day of next month at midnight
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        return next_month.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Invalid period_type: {period_type}")

def get_user_plan(user_id: int) -> PlanType:
    """
    Get user's current plan.
    Maps old plan names to new ones:
    - 'premium' → 'plus'
    - 'vip' → 'pro'
    - None/empty → 'free'
    """
    user = db.get_user(user_id)
    if not user:
        return PLAN_FREE
    
    plan = user.get('plan_type', '').lower()
    
    # Check expiry
    premium_until = user.get('premium_until')
    if premium_until and isinstance(premium_until, str):
         # Handle string (SQLite legacy sometimes) or just in case
         try:
             premium_until = datetime.fromisoformat(premium_until)
         except:
             pass

    if premium_until and isinstance(premium_until, datetime):
        if datetime.utcnow() > premium_until:
            return PLAN_FREE
    
    # Map old names to new system
    if plan == 'premium':
        return PLAN_PLUS
    elif plan == 'vip':
        return PLAN_PRO
    elif plan in [PLAN_PLUS, PLAN_PRO]:
        return plan
    else:
        return PLAN_FREE

def get_usage_status(user_id: int, feature_key: FeatureKey) -> Dict:
    """
    Get current usage status for a feature without consuming.
    Returns: {
        'plan': str,
        'limit': int | None,
        'used': int,
        'remaining': int | None,
        'period': str,
        'reset_at': datetime
    }
    """
    plan = get_user_plan(user_id)
    feature_config = PLAN_LIMITS[plan].get(feature_key)
    
    # Secure fallback if feature key missing (safety)
    if not feature_config:
         return {
            'plan': plan,
            'limit': 0,
            'used': 0,
            'remaining': 0,
            'period': 'day',
            'reset_at': None
        }

    limit = feature_config['limit']
    period = feature_config['period']
    
    # Unlimited check
    if limit is None:
        return {
            'plan': plan,
            'limit': None,
            'used': 0,
            'remaining': None,  # unlimited
            'period': period,
            'reset_at': None
        }
    
    # Get current usage
    period_start = get_period_start(period)
    reset_at = get_reset_datetime(period)
    
    usage_row = db.db.execute(
        """
        SELECT used_count FROM usage_counters
        WHERE user_id = %s AND feature_key = %s 
        AND period_type = %s AND period_start = %s
        """,
        (user_id, feature_key, period, period_start)
    ).fetchone()
    
    used = usage_row[0] if usage_row else 0
    remaining = max(0, limit - used)
    
    return {
        'plan': plan,
        'limit': limit,
        'used': used,
        'remaining': remaining,
        'period': period,
        'reset_at': reset_at
    }

def check_and_consume(user_id: int, feature_key: FeatureKey) -> Dict:
    """
    Check if user can use feature and consume 1 usage if allowed.
    Returns: {
        'allowed': bool,
        'plan': str,
        'limit': int | None,
        'used': int,
        'remaining': int | None,
        'period': str,
        'reset_at': datetime,
        'message_uz': str  (if blocked)
    }
    """
    status = get_usage_status(user_id, feature_key)
    
    # Unlimited access
    if status['limit'] is None:
        return {**status, 'allowed': True}
    
    # Check if limit reached
    if status['remaining'] is not None and status['remaining'] <= 0:
        # Blocked - return upsell info
        upgrade_to = PLAN_PLUS if status['plan'] == PLAN_FREE else PLAN_PRO
        
        # Default messages for common features
        messages = {
            'menu_generate': f"Shaxsiy ovqat menyusi faqat {upgrade_to.capitalize()} tarifida mavjud.",
            'workout_generate': f"Shaxsiy mashq rejasi faqat {upgrade_to.capitalize()} tarifida mavjud.",
            'calorie_scan': f"Bugungi kaloriya tahlil limiti tugadi. {'Cheksiz tahlil uchun Pro tarifiga o\'ting' if upgrade_to == PLAN_PRO else 'Tahlil qilish uchun Plus tarifiga o\'ting'}.",
            'ai_chat': f"AI murabbiy bilan suhbat limiti tugadi. {'Cheksiz suhbat uchun Pro tarifiga o\'ting' if upgrade_to == PLAN_PRO else 'Suhbatlashish uchun Plus tarifiga o\'ting'}.",
            'meal_swap': f"Ovqat almashtirish limiti tugadi. {'Cheksiz almashtirish uchun Pro tarifiga o\'ting' if upgrade_to == PLAN_PRO else 'Kuniga 2 ta almashtirish uchun Plus tarifiga o\'ting'}.",
            'coach_strict_mode': "Qat'iy nazorat rejimi faqat Pro tarifida mavjud.",
        }
        
        # Override specific zero-limit cases for Free plan to match "Not Available" logic
        if status['plan'] == PLAN_FREE:
             messages['calorie_scan'] = "Kaloriya tahlili faqat Plus tarifida mavjud 🌱"
             messages['ai_chat'] = "AI murabbiy faqat Plus tarifida mavjud 🌱"
             messages['meal_swap'] = "Ovqat almashtirish faqat Plus tarifida mavjud 🌱"
             messages['menu_generate'] = "Shaxsiy menyu tuzish faqat Plus tarifida mavjud 🌱"
             messages['workout_generate'] = "Shaxsiy mashq rejasi faqat Plus tarifida mavjud 🌱"

        return {
            **status,
            'allowed': False,
            'upgrade_to': upgrade_to,
            'message_uz': messages.get(feature_key, f"Bu imkoniyat {upgrade_to.capitalize()} tarifida mavjud 🌱")
        }
    
    # Consume 1 usage
    period_start = get_period_start(status['period'])
    
    db.db.execute(
        """
        INSERT INTO usage_counters (user_id, feature_key, period_type, period_start, used_count, created_at, updated_at)
        VALUES (%s, %s, %s, %s, 1, NOW(), NOW())
        ON CONFLICT (user_id, feature_key, period_type, period_start)
        DO UPDATE SET used_count = usage_counters.used_count + 1, updated_at = NOW()
        """,
        (user_id, feature_key, status['period'], period_start)
    )
    db.db.commit()
    
    # Update status after consumption
    status['used'] += 1
    if status['remaining'] is not None:
        status['remaining'] -= 1
    
    return {**status, 'allowed': True}

def get_all_entitlements(user_id: int) -> Dict:
    """
    Get all feature entitlements for user (for API endpoint).
    Returns: {
        'plan': str,
        'active_until': datetime | None,
        'features': {feature_key: {...}}
    }
    """
    user = db.get_user(user_id)
    plan = get_user_plan(user_id)
    active_until = user.get('premium_until') if user else None
    
    features = {}
    for feature_key in ['menu_generate', 'workout_generate', 'calorie_scan', 'ai_chat', 'meal_swap', 'coach_strict_mode']:
        features[feature_key] = get_usage_status(user_id, feature_key)
    
    return {
        'plan': plan,
        'active_until': active_until,
        'features': features
    }
