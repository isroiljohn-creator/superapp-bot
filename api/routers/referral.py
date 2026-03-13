"""Referral API router — stats for Mini App dashboard."""
from fastapi import APIRouter, Header, HTTPException

from api.auth import get_telegram_id_from_init_data
from api.schemas import ReferralStats
from bot.config import settings
from db.database import async_session
from services.crm import CRMService
from services.referral import ReferralService

router = APIRouter(prefix="/referral", tags=["referral"])

# Cache bot username to avoid creating Bot instances per request
_bot_username_cache: str = ""


async def _get_bot_username() -> str:
    global _bot_username_cache
    if not _bot_username_cache:
        from aiogram import Bot
        bot = Bot(token=settings.BOT_TOKEN)
        try:
            bot_info = await bot.get_me()
            _bot_username_cache = bot_info.username
        finally:
            await bot.session.close()
    return _bot_username_cache


@router.get("/stats", response_model=ReferralStats)
async def get_referral_stats(x_telegram_init_data: str = Header(...)):
    """Get referral statistics for user dashboard."""
    telegram_id = get_telegram_id_from_init_data(x_telegram_init_data)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Noto'g'ri autentifikatsiya")

    async with async_session() as session:
        crm = CRMService(session)
        user = await crm.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        ref_service = ReferralService(session)
        stats = await ref_service.get_stats(telegram_id)

        bot_username = await _get_bot_username()
        link = ref_service.generate_link(bot_username, telegram_id)

    amount_for_free = max(0, settings.CLUB_PRICE - stats["balance"])

    return ReferralStats(
        referral_link=link,
        total_invited=stats["total_invited"],
        valid_referrals=stats["valid_referrals"],
        paid_referrals=stats["paid_referrals"],
        balance=stats["balance"],
        club_price=settings.CLUB_PRICE,
        amount_for_free=amount_for_free,
    )
