import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import validate_init_data
from bot.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/team", tags=["team"])

class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    role: str

@router.get("/auth", response_model=UserProfile)
async def check_team_auth(user: dict = Depends(validate_init_data)):
    """Verifies that the incoming Telegram user is an Admin of Nuvi."""
    from db.database import async_session
    from db.models import User
    from sqlalchemy import select
    
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Xizmatga kirish tasdiqlanmadi (initData xato).")
        
    is_team_member = False
    
    # Check DB
    async with async_session() as session:
        res = await session.execute(select(User.is_team_member).where(User.telegram_id == user_id))
        is_team_member = res.scalar() or False
        
    if user_id not in settings.ADMIN_IDS and not is_team_member:
        logger.warning(f"Unauthorized access attempt to Nuvi Team App by User ID: {user_id}")
        raise HTTPException(status_code=403, detail="Siz Nuvi jamoasi ro'yxatida yo'qsiz.")
        
    # Return user details for the frontend profile
    return UserProfile(
        id=user_id,
        first_name=user.get("first_name", "Admin"),
        last_name=user.get("last_name"),
        username=user.get("username"),
        role="Admin/Xodim"
    )
