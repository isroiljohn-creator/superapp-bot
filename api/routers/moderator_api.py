import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from db.database import async_session
from db.models import ModeratedGroup, BannedWord
from api.auth import validate_init_data
from services.tariff import get_effective_plan, get_plan_limits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderator", tags=["moderator"])


class SettingsDTO(BaseModel):
    # Features
    anti_spam: bool
    bad_words_filter: bool
    captcha_enabled: bool
    flood_limit: int
    night_mode: bool
    night_start: str
    night_end: str
    welcome_message: Optional[str]
    warn_limit: int

    # Banned words
    banned_words: List[str]
    
    # Checkbox sub-settings are not natively supported by telegram bot anti-spam yet, 
    # but the frontend expects them. We can ignore them or add them to DB later.
    # For now, we just accept them to not break the frontend format if it sends them.
    model_config = ConfigDict(extra='ignore')


class ModeratorDataResponse(BaseModel):
    group_id: int
    group_title: str
    plan: str
    is_locked: dict  # Map of features -> bool (true if locked)
    settings: SettingsDTO


@router.get("/settings", response_model=ModeratorDataResponse)
async def get_settings(group_id: int, user: dict = Depends(validate_init_data)):
    """Get group moderation settings."""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    async with async_session() as session:
        # Get group
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        grp = result.scalar_one_or_none()

        if not grp:
            raise HTTPException(status_code=404, detail="Guruh topilmadi")

        # Basic security: only 'added_by' or admin list can edit via webapp
        from bot.config import settings as bot_settings
        if grp.added_by != user_id and user_id not in bot_settings.ADMIN_IDS:
            raise HTTPException(status_code=403, detail="Siz bu guruh admini emassiz")

        # Get banned words
        word_result = await session.execute(
            select(BannedWord.word).where(BannedWord.group_id == group_id)
        )
        words = [row[0] for row in word_result.all()]

    plan = get_effective_plan(grp.plan or "free", grp.plan_expires_at)
    limits = get_plan_limits(plan)

    return ModeratorDataResponse(
        group_id=group_id,
        group_title=grp.group_title or str(group_id),
        plan=plan,
        is_locked={
            "flood": not limits.get("flood_control"),
            "night": not limits.get("night_mode"),
            "welcome": not limits.get("welcome_message")
        },
        settings=SettingsDTO(
            anti_spam=grp.anti_spam,
            bad_words_filter=grp.bad_words_filter,
            captcha_enabled=grp.captcha_enabled,
            flood_limit=grp.flood_limit or 10,
            night_mode=grp.night_mode,
            night_start=grp.night_start or "00:00",
            night_end=grp.night_end or "08:00",
            welcome_message=grp.welcome_message or "",
            warn_limit=grp.warn_limit or 3,
            banned_words=words,
        )
    )


@router.post("/settings")
async def save_settings(
    group_id: int, 
    data: SettingsDTO, 
    user: dict = Depends(validate_init_data)
):
    """Save group moderation settings."""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    async with async_session() as session:
        # Get group
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == group_id)
        )
        grp = result.scalar_one_or_none()

        if not grp:
            raise HTTPException(status_code=404, detail="Guruh topilmadi")

        from bot.config import settings as bot_settings
        if grp.added_by != user_id and user_id not in bot_settings.ADMIN_IDS:
            raise HTTPException(status_code=403, detail="Siz bu guruh admini emassiz")

        # Validate plan limits
        plan = get_effective_plan(grp.plan or "free", grp.plan_expires_at)
        limits = get_plan_limits(plan)

        # Update basic settings
        grp.anti_spam = data.anti_spam
        grp.bad_words_filter = data.bad_words_filter
        grp.captcha_enabled = data.captcha_enabled
        grp.warn_limit = data.warn_limit

        # Premium limits
        if limits.get("flood_control"):
            grp.flood_limit = data.flood_limit
        if limits.get("night_mode"):
            grp.night_mode = data.night_mode
            grp.night_start = data.night_start
            grp.night_end = data.night_end
        if limits.get("welcome_message"):
            grp.welcome_message = data.welcome_message

        # Sync banned words (delete all and re-add to handle removes and adds simply)
        from sqlalchemy import delete
        await session.execute(
            delete(BannedWord).where(BannedWord.group_id == group_id)
        )

        max_words = limits.get("max_banned_words", 10)
        words_to_add = data.banned_words[:max_words]
        
        for w in words_to_add:
            w = w.strip().lower()
            if w:
                session.add(BannedWord(
                    group_id=group_id,
                    word=w,
                    added_by=user_id,
                ))

        await session.commit()

    return {"status": "success"}

class UpgradeRequest(BaseModel):
    group_id: int
    plan: str

@router.post("/upgrade")
async def upgrade_plan(data: UpgradeRequest, user: dict = Depends(validate_init_data)):
    """Upgrade group moderation plan pulling from user's unified balance."""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    price_val = 49000 if data.plan == "pro" else 149000 if data.plan == "vip" else 0
    if price_val == 0:
        raise HTTPException(status_code=400, detail="Noto'g'ri tarif")
        
    price_text = f"{price_val:,.0f} so'm"
    plan_name = data.plan.capitalize()

    async with async_session() as session:
        from services.crm import CRMService
        from db.models import User
        from sqlalchemy import update
        from datetime import datetime, timezone, timedelta
        
        crm = CRMService(session)
        db_user = await crm.get_user(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

        balance = float(db_user.tokens or 0)
        if balance < price_val:
            raise HTTPException(status_code=400, detail="Hisobingizda yetarli mablag' yo'q!")

        # Verify group ownership/admin
        result = await session.execute(
            select(ModeratedGroup).where(ModeratedGroup.group_id == data.group_id)
        )
        grp = result.scalar_one_or_none()
        if not grp:
            raise HTTPException(status_code=404, detail="Guruh topilmadi")
            
        from bot.config import settings as bot_settings
        if grp.added_by != user_id and user_id not in bot_settings.ADMIN_IDS:
            raise HTTPException(status_code=403, detail="Siz bu guruh admini emassiz")

        # Deduct balance
        await session.execute(
            update(User).where(User.id == db_user.id).values(tokens=User.tokens - price_val)
        )

        # Update group plan
        expiry = datetime.now(timezone.utc) + timedelta(days=30)
        await session.execute(
            update(ModeratedGroup)
            .where(ModeratedGroup.group_id == data.group_id)
            .values(
                plan=data.plan,
                plan_expires_at=expiry,
                anti_spam=True,
                bad_words_filter=True,
                captcha_enabled=(data.plan == "vip"),
            )
        )
        await session.commit()
        
        # Send Telegram notification
        try:
            from api.main import bot
            import html as html_mod
            safe_name = html_mod.escape(user.get("first_name") or "")
            
            # Message to user
            try:
                if bot:
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"✅ <b>Tarif muvaffaqiyatli xarid qilindi!</b>\n\n"
                            f"🏢 Guruh: <code>{grp.group_title or data.group_id}</code>\n"
                            f"Sizning <b>{plan_name}</b> tarifingiz faollashdi.\n"
                            f"Balansdan <b>{price_text}</b> yechib olindi.\n\n"
                            f"Barcha premium funksiyalar guruhingiz uchun ishlashni boshladi! 🎉"
                        ),
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Failed to send confirmation to user: {e}")

            # Message to admins
            for aid in bot_settings.ADMIN_IDS:
                try:
                    if bot:
                        await bot.send_message(
                            chat_id=aid,
                            text=(
                                f"💳 <b>Yangi Tarif xaridi (MiniApp dan)!</b>\n\n"
                                f"👤 {safe_name}\n"
                                f"🏢 Guruh ID: <code>{data.group_id}</code>\n"
                                f"💳 Tarif: {plan_name}\n"
                                f"💰 To'landi: {price_text} (Ichki balansdan)"
                            ),
                            parse_mode="HTML",
                        )
                except Exception:
                    pass
        except Exception:
            pass

    return {"status": "success"}
