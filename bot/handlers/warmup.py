"""7-day warmup (progrev) content sequence — pre-tripwire nurture.

Fires once, right after segmentation + lead magnet delivery. Day-by-day copy
can be overridden per day via AdminSetting key "warmup_day_{day}"; falls back
to the uz.WARMUP_DAY_N constants. Mirrors bot/handlers/subscription.py's
handle_churn override pattern.
"""
import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.locales import uz

logger = logging.getLogger(__name__)

_DAY_FALLBACK = {
    1: uz.WARMUP_DAY_1,
    2: uz.WARMUP_DAY_2,
    3: uz.WARMUP_DAY_3,
    4: uz.WARMUP_DAY_4,
    5: uz.WARMUP_DAY_5,
    6: uz.WARMUP_DAY_6,
    7: uz.WARMUP_DAY_7,
}


async def handle_warmup_day(bot: Bot, telegram_id: int, day: int):
    """Send the warmup message for the given day (1-7)."""
    from db.database import async_session
    from db.models import AdminSetting
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(AdminSetting.value).where(AdminSetting.key == f"warmup_day_{day}")
        )
        custom_text = result.scalar_one_or_none()

    text = custom_text or _DAY_FALLBACK.get(day, "")
    if not text:
        return

    kb = None
    if day == 7:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 AI START — 149,000 so'm", callback_data="tripwire:buy")]
        ])

    await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML", reply_markup=kb)
