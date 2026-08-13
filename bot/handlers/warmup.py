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
    """Send the warmup message for the given day (1-7).

    Days 1/2/5/6 reference showing something visual ("ko'rsataman"); if the
    admin has attached a photo/video for that day via AdminSetting keys
    "warmup_day_{day}_media"/"warmup_day_{day}_media_type", it's sent with
    the text as caption. Otherwise falls back to a plain text message —
    nothing breaks if no media was ever configured.
    """
    from db.database import async_session
    from db.models import AdminSetting
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(AdminSetting.key, AdminSetting.value).where(
                AdminSetting.key.in_([
                    f"warmup_day_{day}",
                    f"warmup_day_{day}_media",
                    f"warmup_day_{day}_media_type",
                ])
            )
        )
        rows = dict(result.all())

    text = rows.get(f"warmup_day_{day}") or _DAY_FALLBACK.get(day, "")
    if not text:
        return

    kb = None
    if day == 7:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 AI START — 149,000 so'm", callback_data="tripwire:buy")]
        ])

    media_file_id = rows.get(f"warmup_day_{day}_media")
    media_type = rows.get(f"warmup_day_{day}_media_type") or "photo"

    if media_file_id:
        try:
            if media_type == "video":
                await bot.send_video(chat_id=telegram_id, video=media_file_id, caption=text, parse_mode="HTML", reply_markup=kb)
            else:
                await bot.send_photo(chat_id=telegram_id, photo=media_file_id, caption=text, parse_mode="HTML", reply_markup=kb)
            return
        except Exception as e:
            logger.warning(f"Warmup day {day} media send failed, falling back to text: {e}")

    await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML", reply_markup=kb)
