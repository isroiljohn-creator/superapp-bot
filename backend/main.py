import os
import hmac
import hashlib
from urllib.parse import parse_qsl
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, init_db
from backend.models import User, DailyLog, Plan, Transaction
from backend.auth import create_access_token, get_current_user
from core.ai import call_gemini, format_ai_text
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

app = FastAPI(title="YASHA v2.0 API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Pydantic Models ===

class TelegramAuthRequest(BaseModel):
    initData: str

class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None
    allergies: Optional[str] = None

class DailyTaskUpdate(BaseModel):
    task_type: str  # water, workout, steps
    value: bool | int

class BroadcastRequest(BaseModel):
    message: str
    filter: Optional[dict] = None

# === Startup ===

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("✅ Database initialized")

# === Auth Endpoints ===

@app.post("/auth/telegram")
async def telegram_auth(req: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Telegram WebApp initData"""
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not set")

    try:
        parsed_data = dict(parse_qsl(req.initData))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid initData format")
    
    if "hash" not in parsed_data:
        raise HTTPException(status_code=401, detail="Missing hash")

    hash_ = parsed_data.pop("hash")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != hash_:
        raise HTTPException(status_code=403, detail="Invalid hash")

    import json
    user_data = json.loads(parsed_data.get("user", "{}"))
    telegram_id = user_data.get("id")
    
    # Get or create user
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Auto-create user (phone will be added later via bot or profile update)
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            full_name=user_data.get("first_name", "") + " " + user_data.get("last_name", ""),
            phone=None,  # Phone will be added during bot onboarding or profile update
            referral_code=f"r{telegram_id}"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Generate JWT token
    token = create_access_token({"user_id": user.id, "telegram_id": telegram_id})
    
    is_admin = telegram_id == ADMIN_ID
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "is_premium": user.is_premium,
            "is_admin": is_admin
        }
    }

# === User Endpoints ===

@app.get("/user/profile")
async def get_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get user profile"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "username": user.username,
        "age": user.age,
        "gender": user.gender,
        "height": user.height,
        "weight": user.weight,
        "target_weight": user.target_weight,
        "goal": user.goal,
        "allergies": user.allergies,
        "is_premium": user.is_premium,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "points": user.points,
        "referral_code": user.referral_code
    }

@app.put("/user/profile")
async def update_profile(
    update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    await db.commit()
    return {"status": "updated"}

# === AI Endpoints ===

@app.post("/ai/workout")
async def generate_workout(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate AI workout plan"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check premium for full plan
    if not user.is_premium:
        return {"plan": "⚠️ Premium kerak. Free foydalanuvchilar uchun cheklangan.", "is_preview": True}
    
    prompt = f"""Create a 4-day workout plan for a {user.age} year old {user.gender} person.
Goal: {user.goal}. Keep it short, bold titles, bullet points, max 800 characters."""
    
    plan_text = call_gemini(prompt)
    if not plan_text:
        plan_text = "Mashq rejasi yuklanmadi. Keyinroq urinib ko'ring."
    
    formatted = format_ai_text(plan_text, "Haftalik Mashq Rejasi")
    
    # Save to database
    plan = Plan(user_id=user.id, type="workout", content=formatted)
    db.add(plan)
    await db.commit()
    
    return {"plan": formatted, "is_preview": False}

@app.post("/ai/meal")
async def generate_meal(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate AI meal plan"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_premium:
        return {"plan": "⚠️ Premium kerak. Free versiyada cheklangan.", "is_preview": True}
    
    prompt = f"""Create a 7-day meal plan for {user.age} year old {user.gender}.
Goal: {user.goal}. Uzbek cuisine. Allergies: {user.allergies or 'None'}.
Short, bold titles, max 800 characters."""
    
    plan_text = call_gemini(prompt)
    if not plan_text:
        plan_text = "Menyu yuklanmadi."
    
    formatted = format_ai_text(plan_text, "Haftalik Ovqat Rejasi")
    
    plan = Plan(user_id=user.id, type="meal", content=formatted)
    db.add(plan)
    await db.commit()
    
    return {"plan": formatted, "is_preview": False}

# === Premium & Referral ===

@app.get("/premium/status")
async def premium_status(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Check premium status"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    
    return {
        "is_premium": user.is_premium,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None
    }

@app.get("/referral/info")
async def referral_info(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get referral info"""
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()
    
    # Count referrals
    count_result = await db.execute(select(func.count()).select_from(User).where(User.referrer_id == user.id))
    count = count_result.scalar()
    
    bot_username = os.getenv("BOT_USERNAME", "YashaBot")
    link = f"https://t.me/{bot_username}?start={user.referral_code}"
    
    return {
        "link": link,
        "count": count,
        "points": user.points
    }

# === Analytics ===

@app.get("/analytics/daily")
async def get_daily_logs(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get daily activity logs"""
    result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == current_user["user_id"]).order_by(DailyLog.date.desc()).limit(days)
    )
    logs = result.scalars().all()
    
    return {"logs": [{"date": log.date, "water": log.water_drank, "workout": log.workout_done, "steps": log.steps_count} for log in logs]}

# === Admin Endpoints ===

@app.get("/admin/stats")
async def admin_stats(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get admin statistics"""
    if current_user["telegram_id"] != ADMIN_ID:
        raise HTTPException(status_code=403, detail="Admin only")
    
    total = await db.execute(select(func.count()).select_from(User))
    premium = await db.execute(select(func.count()).select_from(User).where(User.is_premium == True))
    
    return {
        "total_users": total.scalar(),
        "premium_users": premium.scalar()
    }

# === Static Files ===

app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA"""
    if full_path.startswith("api/") or full_path.startswith("auth/") or full_path.startswith("user/") or full_path.startswith("ai/") or full_path.startswith("premium/") or full_path.startswith("referral/") or full_path.startswith("analytics/") or full_path.startswith("admin/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    file_path = f"frontend/dist/{full_path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    return FileResponse("frontend/dist/index.html")
