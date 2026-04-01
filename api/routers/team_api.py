import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import validate_init_data
from bot.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/team", tags=["team"])

from typing import Optional
from api.auth import last_auth_errors

# Global variable to capture debug info
last_auth_attempt = {"data": None, "error": None}

class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    role: str

@router.get("/debug")
async def get_team_debug():
    return {
        "auth_errors": last_auth_errors[-10:],
        "team_api_errors": last_auth_attempt
    }

@router.get("/auth", response_model=UserProfile)
async def check_team_auth(user: dict = Depends(validate_init_data)):
    """Verifies that the incoming Telegram user is an Admin of Nuvi."""
    from db.database import async_session
    from db.models import User
    from sqlalchemy import select
    
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Xizmatga kirish tasdiqlanmadi (initData xato).")
        
    try:
        user_id = int(user_id)
    except:
        pass
        
    is_team_member = False
    
    # Check DB
    try:
        async with async_session() as session:
            res = await session.execute(select(User.is_team_member).where(User.telegram_id == user_id))
            is_team_member = res.scalar() or False
    except Exception as e:
        logger.error(f"DB Error fetching team member: {e}")
        
    if user_id not in settings.ADMIN_IDS and not is_team_member:
        err = f"Unauthorized access attempt to Nuvi Team App by User ID: {user_id}"
        logger.warning(err)
        last_auth_attempt["error"] = err
        raise HTTPException(status_code=403, detail="Siz Nuvi jamoasi ro'yxatida yo'qsiz.")
        
    # Return user details for the frontend profile
    return UserProfile(
        id=user_id,
        first_name=user.get("first_name", "Admin"),
        last_name=user.get("last_name"),
        username=user.get("username"),
        role="Admin/Xodim"
    )
