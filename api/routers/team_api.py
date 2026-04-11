import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from api.auth import validate_init_data
from bot.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/team", tags=["team"])

from typing import Optional
from api.auth import last_auth_errors
from api.auth_jwt import get_current_admin

# Global variable to capture debug info
last_auth_attempt = {"data": None, "error": None}

class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    role: str

@router.get("/auth", response_model=UserProfile)
async def check_team_auth(
    authorization: str = Header(default=""),
    init_data: str = ""
):
    """Verifies that the incoming user is an Admin/Team member."""
    
    if authorization.lower().startswith("bearer "):
        # JWT Flow
        try:
            admin_data = await get_current_admin(authorization)
            return UserProfile(
                id=admin_data.get("id", 0),
                first_name=admin_data.get("username", "Admin"),
                last_name="",
                username=admin_data.get("username", "Admin"),
                role="Admin/Xodim"
            )
        except Exception as e:
            raise e
            
    # Telegram Auth Flow
    try:
        user = validate_init_data(authorization, init_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Xizmatga kirish tasdiqlanmadi.")
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
