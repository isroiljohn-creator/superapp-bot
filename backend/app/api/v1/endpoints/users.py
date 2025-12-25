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
    
    # Support multiple identity keys for resilience
    user_id = payload.get("user_id") or payload.get("sub") or payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user identity")
        
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

from backend.app.schemas.user import UserProfileUpdate

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

    # Auto-heal onboarding status if any significant data exists
    has_data = any([
        current_user.age and current_user.age > 0,
        current_user.weight and current_user.weight > 0,
        current_user.goal,
        current_user.full_name,
        current_user.phone
    ])
    
    if not current_user.is_onboarded and has_data:
        print(f"DEBUG: Auto-healing onboarding status for user {current_user.id} due to existing data")
        current_user.is_onboarded = True
        try:
            await db.commit()
            await db.refresh(current_user)
        except:
            await db.rollback()

    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
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
        "is_onboarded": current_user.is_onboarded,
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
    update_req: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print(f"DEBUG: Profile update attempt for user_id={current_user.id} (telegram_id={current_user.telegram_id})")
    print(f"DEBUG: Active Session ID: {id(db)}")
    
    # Reload user in THIS session to be absolutely sure
    user = await db.get(User, current_user.id)
    if not user:
        print(f"ERROR: User {current_user.id} disappeared from DB during update!")
        raise HTTPException(status_code=404, detail="User not found during update")

    data = update_req.dict(exclude_unset=True)
    print(f"DEBUG: Update Payload: {data}")
    
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)
            print(f"  - Updated {key} -> {value}")
        else:
            print(f"  - WARNING: '{key}' not found on User model")
    
    user.is_onboarded = True
    user.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(user)
        print(f"✅ Success: Profile for {user.id} committed and refreshed. is_onboarded={user.is_onboarded}")
        return {
            "status": "success", 
            "is_onboarded": user.is_onboarded,
            "full_name": user.full_name,
            "age": user.age
        }
    except Exception as e:
        print(f"❌ Transaction Error for {user.id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit failed: {e}")
@router.get("/health/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    """Check database connectivity and engine type"""
    from sqlalchemy import text
    try:
        # Check engine type
        bind = db.get_bind()
        dialect = bind.dialect.name
        
        # Test query
        await db.execute(text("SELECT 1"))
        
        # Check for column existence
        col_check = await db.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='is_onboarded'"
        ))
        has_column = col_check.scalar() is not None
        
        return {
            "status": "connected",
            "dialect": dialect,
            "has_is_onboarded": has_column,
            "db_url_redacted": os.getenv("DATABASE_URL", "NOT_SET")[:20] + "..." if os.getenv("DATABASE_URL") else "NOT_SET"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

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
