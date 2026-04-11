"""User API router — profile endpoint for Mini App."""
from fastapi import APIRouter, Header, HTTPException

from api.auth import validate_init_data, get_telegram_id_from_init_data
from api.schemas import UserProfile
from db.database import async_session
from services.crm import CRMService
from services.subscription import SubscriptionService

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(x_telegram_init_data: str = Header(...)):
    """Get user profile from Telegram initData."""
    telegram_id = get_telegram_id_from_init_data(x_telegram_init_data)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri autentifikatsiya")

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        sub_service = SubscriptionService(session)
        is_active = await sub_service.is_active(user.id)
        await session.commit()  # persist any expire() side-effects from is_active

    return UserProfile(
        telegram_id=user.telegram_id,
        name=user.name,
        age=user.age,
        goal_tag=user.goal_tag,
        level_tag=user.level_tag,
        lead_score=user.lead_score,
        lead_segment=user.lead_segment,
        user_status=user.user_status,
        subscription_status="active" if is_active else "inactive",
        registered_at=user.registered_at.isoformat() if user.registered_at else None,
    )

from pydantic import BaseModel

class LandingLeadRequest(BaseModel):
    name: str
    phone: str
    referer_id: int | None = None

@router.post("/landing-lead")
async def register_landing_lead(req: LandingLeadRequest):
    """Save a lead submitted from the external landing page."""
    from db.models import User
    import time
    
    async with async_session() as session:
        # Create a mock telegram_id since they register outside of Telegram
        # We use a negative timestamp ID to mark external web leads
        ext_id = -int(time.time() * 1000)
        
        new_user = User(
            telegram_id=ext_id,
            name=req.name,
            phone=req.phone,
            source="landing_page",
            campaign="ai_kurs",
            referer_id=req.referer_id,
            user_status="registered",
            lead_segment="hot",
            lead_score=50
        )
        session.add(new_user)
        await session.commit()
        
    return {"status": "success", "message": "Ro'yxatdan o'tish muvaffaqiyatli"}
