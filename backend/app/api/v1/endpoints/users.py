from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models import User
from backend.auth import verify_token
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    allergies: Optional[str] = None

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Fetch today's log for stats
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    from backend.models import DailyLog
    from sqlalchemy import select
    
    log_result = await db.execute(
        select(DailyLog).where(DailyLog.user_id == current_user.id, DailyLog.date == today)
    )
    today_log = log_result.scalar_one_or_none()

    return {
        "id": current_user.id,
        "username": current_user.username,
        "age": current_user.age,
        "gender": current_user.gender,
        "height": current_user.height,
        "weight": current_user.weight,
        "target_weight": current_user.target_weight,
        "goal": current_user.goal,
        "activity_level": current_user.activity_level,
        "allergies": current_user.allergies,
        "is_premium": current_user.is_premium,
        "premium_until": current_user.premium_until,
        "points": current_user.points,
        "plan_type": current_user.plan_type,
        "streak_water": current_user.streak_water,
        "streak_sleep": current_user.streak_sleep,
        "streak_mood": current_user.streak_mood,
        "referral_code": current_user.referral_code,
        "bot_username": os.getenv("BOT_USERNAME", "yashabot"),
        "today_water": today_log.water_ml if today_log else 0,
        "today_steps": today_log.steps if today_log else 0,
        "today_sleep": today_log.sleep_hours if today_log else 0
    }

@router.put("/profile")
async def update_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    for key, value in update.dict(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    await db.commit()
@router.post("/reset")
async def reset_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user profile data"""
    current_user.age = None
    # gender usually kept or reset? User asked to "delete data". 
    # If we reset gender, onboarding flows again.
    current_user.gender = None 
    current_user.height = None
    current_user.weight = None
    current_user.target_weight = None
    current_user.goal = None
    current_user.activity_level = None
    current_user.allergies = None
    current_user.is_onboarded = False # Ensure onboarding shows again if your logic determines onboarding by these fields
    
    # Also clear logs? The user said "Delete Data". 
    # Usually "Delete Data" implies clearing history too.
    # But for now, let's stick to Profile Reset as that's what shows in the "Profile" card in Mini App.
    # The user screenshot showed Profile Card with data.
    
    await db.commit()
    return {"status": "reset"}
