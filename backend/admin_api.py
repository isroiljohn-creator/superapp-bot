import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl, unquote
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy import select, func, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from backend.database import get_db
from backend.models import User, DailyLog, Plan, Transaction, Feedback, MenuFeedback, WorkoutFeedback, CoachFeedback, UserAdaptationState, AIUsageLog, AdminEvent
from core.config import BOT_TOKEN, ADMIN_IDS
from backend.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Schemas ---

class TelegramAuthRequest(BaseModel):
    initData: str

class TokenResponse(BaseModel):
    token: str
    user: dict

# --- Auth Helper ---

def verify_telegram_data(init_data: str) -> dict:
    """
    Verifies Telegram WebApp initData string provided by the frontend.
    Returns the parsed user dict if valid and authorized.
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    if "hash" not in parsed_data:
        raise HTTPException(status_code=400, detail="Missing hash")

    hash_check = parsed_data.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_check:
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Time check (optional but recommended)
    auth_date = int(parsed_data.get("auth_date", 0))
    if time.time() - auth_date > 86400: # 24h expiry
         raise HTTPException(status_code=403, detail="initData expired")

    user_data = json.loads(parsed_data.get("user", "{}"))
    user_id = user_data.get("id")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID missing in data")

    # Admin Allowlist Check
    # Convert everything to string for comparison to avoid int/string mismatches
    str_admin_ids = [str(aid) for aid in ADMIN_IDS]
    str_user_id = str(user_id)
    
    if str_user_id not in str_admin_ids:
        print(f"❌ ADMIN ACCESS DENIED: User ID {user_id} ({type(user_id)}) not in allowlist {ADMIN_IDS} (types: {[type(x) for x in ADMIN_IDS]})")
        raise HTTPException(status_code=403, detail="Admin access restricted")

    print(f"✅ ADMIN ACCESS GRANTED: User ID {user_id}")
    return user_data

# --- Dependency ---

async def get_current_admin(authorization: str = Header(...)):
    """
    Validates JWT and ensures admin role.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        return int(user_id)
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- Endpoints ---

@router.post("/auth/telegram", response_model=TokenResponse)
async def auth_telegram(req: TelegramAuthRequest):
    """
    Exchanges WebApp initData for a Backend JWT.
    """
    user_data = verify_telegram_data(req.initData)
    user_id = user_data["id"]
    
    # Create JWT
    expires = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": str(user_id),
        "role": "admin",
        "exp": expires
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "token": token,
        "user": user_data
    }

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Investor KPI Snapshot
    """
    # Totals
    total_users_q = await db.execute(select(func.count(User.id)))
    total_users = total_users_q.scalar() or 0
    
    premium_q = await db.execute(select(func.count(User.id)).where(User.is_premium == True))
    premium = premium_q.scalar() or 0
    
    # Active Users (Approximation via feedback/logs)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # DAU (Feedback + AI Logs)
    dau_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
        ) t
    """), {"d": one_day_ago})
    dau = dau_q.scalar() or 0
    
    # WAU
    wau_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
        ) t
    """), {"d": seven_days_ago})
    wau = wau_q.scalar() or 0
    
    # MAU (30d)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    mau_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM ai_usage_logs WHERE timestamp >= :d
        ) t
    """), {"d": thirty_days_ago})
    mau = mau_q.scalar() or 0
    
    # Menu Generations (24h)
    # Using AI Usage Logs feature='menu'
    menu_gen_q = await db.execute(select(func.count()).where(AIUsageLog.feature == 'menu', AIUsageLog.timestamp >= one_day_ago))
    menu_gen = menu_gen_q.scalar() or 0
    
    workout_gen_q = await db.execute(select(func.count()).where(AIUsageLog.feature == 'workout', AIUsageLog.timestamp >= one_day_ago))
    workout_gen = workout_gen_q.scalar() or 0
    
    # New Users 24h
    new_users_q = await db.execute(select(func.count()).where(User.created_at >= one_day_ago))
    new_users = new_users_q.scalar() or 0

    return {
        "total_users": total_users,
        "active_24h": dau,
        "active_7d": wau,
        "active_30d": mau,
        "premium_users": premium,
        "free_users": total_users - premium,
        "trial_users": 0, # Placeholder until trial logic is fully integrated
        "new_users_24h": new_users,
        "menu_generations_24h": menu_gen,
        "workout_generations_24h": workout_gen
    }

@router.get("/feedback")
async def get_feedback_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Feedback metrics (7d)
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Unique Users 7d
    uniq_q = await db.execute(text("""
        SELECT count(distinct user_id) FROM (
            SELECT user_id FROM menu_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM workout_feedback WHERE created_at >= :d
            UNION
            SELECT user_id FROM coach_feedback WHERE created_at >= :d
        ) t
    """), {"d": seven_days_ago})
    unique_users = uniq_q.scalar() or 0
    
    # Distributions
    def get_dist(table):
        return text(f"SELECT rating, count(*) FROM {table} WHERE created_at >= :d GROUP BY rating ORDER BY 2 DESC")
        
    menu_dist = (await db.execute(get_dist("menu_feedback"), {"d": seven_days_ago})).fetchall()
    workout_dist = (await db.execute(get_dist("workout_feedback"), {"d": seven_days_ago})).fetchall()
    
    # Top Coach Messages
    top_coach = (await db.execute(text("""
        SELECT coach_msg_key, category, count(*) FROM coach_feedback 
        WHERE reaction='love' AND created_at >= :d 
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5
    """), {"d": seven_days_ago})).fetchall()

    def list_to_dict(rows):
        return {r[0]: r[1] for r in rows}

    return {
        "menu": {
            **list_to_dict(menu_dist),
            "users": (await db.execute(text("SELECT count(distinct user_id) FROM menu_feedback WHERE created_at >= :d"), {"d": seven_days_ago})).scalar() or 0
        },
        "workout": {
            **list_to_dict(workout_dist),
            "users": (await db.execute(text("SELECT count(distinct user_id) FROM workout_feedback WHERE created_at >= :d"), {"d": seven_days_ago})).scalar() or 0
        },
        "coach": {
            "love": (await db.execute(text("SELECT count(*) FROM coach_feedback WHERE reaction='love' AND created_at >= :d"), {"d": seven_days_ago})).scalar() or 0,
            "like": (await db.execute(text("SELECT count(*) FROM coach_feedback WHERE reaction='like' AND created_at >= :d"), {"d": seven_days_ago})).scalar() or 0,
            "meh": (await db.execute(text("SELECT count(*) FROM coach_feedback WHERE reaction='meh' AND created_at >= :d"), {"d": seven_days_ago})).scalar() or 0,
            "users": (await db.execute(text("SELECT count(distinct user_id) FROM coach_feedback WHERE created_at >= :d"), {"d": seven_days_ago})).scalar() or 0
        },
        "top_loved_coach": [{"coach_msg_key": r[0], "category": r[1], "love": r[2]} for r in top_coach]
    }

@router.get("/adaptation")
async def get_adaptation_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    Adaptation metrics
    """
    # Total adapted
    total_q = await db.execute(select(func.count(UserAdaptationState.user_id)))
    total = total_q.scalar() or 0
    
    # Recent (7d) - updated_at
    d7 = datetime.utcnow() - timedelta(days=7)
    recent_q = await db.execute(select(func.count(UserAdaptationState.user_id)).where(UserAdaptationState.updated_at >= d7))
    recent = recent_q.scalar() or 0
    
    # Variant Preference
    var_q = await db.execute(select(UserAdaptationState.menu_variant_preference, func.count()).group_by(UserAdaptationState.menu_variant_preference))
    variants = var_q.fetchall()
    
    # Soft Mode
    soft_q = await db.execute(select(func.count()).where(UserAdaptationState.workout_soft_mode == True))
    soft = soft_q.scalar() or 0
    
    # Validation Metric: Bad Feedback -> Adaptation (Diet Switch)
    val_q = await db.execute(text("""
        SELECT
          COUNT(DISTINCT mf.user_id) AS complained,
          COUNT(DISTINCT uas.user_id) AS adapted
        FROM (
          SELECT user_id, created_at FROM menu_feedback 
          WHERE rating = 'bad' AND created_at >= now() - interval '7 days'
        ) mf
        JOIN user_adaptation_state uas ON uas.user_id = mf.user_id
        WHERE uas.updated_at >= mf.created_at
           OR uas.menu_kcal_adjust_pct < 0
    """))
    val = val_q.fetchone()
    
    return {
        "adapted_users_total": total,
        "adapted_users_7d": recent,
        "variants": [{"type": r[0] or "none", "count": r[1]} for r in variants],
        "soft_mode_count": soft,
        "validation_7d": {
            "complained": val.complained if val else 0,
            "adapted": val.adapted if val else 0
        }
    }

@router.get("/cost")
async def get_cost_stats(db: AsyncSession = Depends(get_db), admin_id: int = Depends(get_current_admin)):
    """
    AI Cost metrics (from ai_usage_logs)
    """
    def get_sums(days):
        d = datetime.utcnow() - timedelta(days=days)
        return text("""
            SELECT 
                SUM(total_tokens),
                SUM(cost_usd),
                SUM(CASE WHEN feature='menu' THEN cost_usd ELSE 0 END),
                SUM(CASE WHEN feature='workout' THEN cost_usd ELSE 0 END),
                SUM(CASE WHEN feature='chat' THEN cost_usd ELSE 0 END)
            FROM ai_usage_logs
            WHERE timestamp >= :d
        """)
        
    res_24h = (await db.execute(get_sums(1), {"d": datetime.utcnow() - timedelta(days=1)})).fetchone()
    res_7d = (await db.execute(get_sums(7), {"d": datetime.utcnow() - timedelta(days=7)})).fetchone()
    res_30d = (await db.execute(get_sums(30), {"d": datetime.utcnow() - timedelta(days=30)})).fetchone()
    
    def fmt_feature(feature_name, result):
        if not result: return {"feature": feature_name, "tokens": 0, "cost_usd": 0}
        return {
            "feature": feature_name,
            "tokens": result[0] or 0,
            "cost_usd": result[1] or 0
        }

    # By Feature breakdown
    def get_feature_totals(feature, days):
        d = datetime.utcnow() - timedelta(days=days)
        return text(f"SELECT SUM(total_tokens), SUM(cost_usd) FROM ai_usage_logs WHERE feature=:f AND timestamp >= :d")

    menu_total = (await db.execute(get_feature_totals('menu', 7), {"f": 'menu', "d": datetime.utcnow() - timedelta(days=7)})).fetchone()
    workout_total = (await db.execute(get_feature_totals('workout', 7), {"f": 'workout', "d": datetime.utcnow() - timedelta(days=7)})).fetchone()
    chat_total = (await db.execute(get_feature_totals('chat', 7), {"f": 'chat', "d": datetime.utcnow() - timedelta(days=7)})).fetchone()

    # Daily breakdown (last 7 days)
    daily_stats = []
    for i in range(6, -1, -1):
        day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        res = (await db.execute(text("SELECT SUM(total_tokens), SUM(cost_usd) FROM ai_usage_logs WHERE timestamp >= :s AND timestamp < :e"), {"s": day_start, "e": day_end})).fetchone()
        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "tokens": res[0] or 0,
            "cost_usd": res[1] or 0
        })

    return {
        "total_tokens": res_7d[0] or 0,
        "total_cost_usd": res_7d[1] or 0,
        "by_feature": [
            fmt_feature('menu', menu_total),
            fmt_feature('workout', workout_total),
            fmt_feature('coach', chat_total)
        ],
        "daily": daily_stats
    }
