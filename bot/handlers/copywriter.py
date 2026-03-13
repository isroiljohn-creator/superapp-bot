"""Copywriter handler — Gemini API for text generation."""
import logging
import json
import urllib.request
import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.locales import uz
from bot.keyboards.buttons import main_menu_keyboard, ai_workers_reply_keyboard
from bot.config import settings
from db.database import async_session
from services.token_service import spend_tokens_async, get_tokens_async, add_tokens_async, COPY_COST

router = Router(name="copywriter")
logger = logging.getLogger("copywriter")

# ── FSM States ────────────────────────────────
class CopywriterStates(StatesGroup):
    waiting_type = State()
    waiting_prompt = State()

# ── Copy types ────────────────────────────────
COPY_TYPES = {
    "copy:post": ("📱 Post yozish", "ijtimoiy tarmoqlar uchun qiziqarli post"),
    "copy:ad": ("📢 Reklama matni", "ta'sirli reklama matni"),
    "copy:email": ("📧 Email shablon", "professional email"),
    "copy:desc": ("📋 Mahsulot tavsifi", "sotuvchi mahsulot tavsifi"),
}


def copy_type_keyboard() -> InlineKeyboardMarkup:
    """Copy type selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=uz.COPYWRITER_TYPES_POST, callback_data="copy:post")],
        [InlineKeyboardButton(text=uz.COPYWRITER_TYPES_AD, callback_data="copy:ad")],
        [InlineKeyboardButton(text=uz.COPYWRITER_TYPES_EMAIL, callback_data="copy:email")],
        [InlineKeyboardButton(text=uz.COPYWRITER_TYPES_DESC, callback_data="copy:desc")],
        [InlineKeyboardButton(text=uz.AI_WORKERS_BTN_BACK, callback_data="aiw:back")],
    ])


def _call_gemini(prompt: str) -> str:
    """Call Gemini API synchronously (run in thread)."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 1024,
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
    })

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    # Extract text from response
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            return parts[0].get("text", "")

    raise ValueError("Gemini returned empty response")


# ── Copy type selection ──────────────────────
@router.callback_query(F.data.in_({"copy:post", "copy:ad", "copy:email", "copy:desc"}))
async def select_copy_type(callback_query: CallbackQuery, state: FSMContext):
    """User selected a copy type."""
    copy_type_id = callback_query.data
    if copy_type_id not in COPY_TYPES:
        return

    type_name, type_desc = COPY_TYPES[copy_type_id]
    await state.update_data(copy_type=type_name, copy_desc=type_desc)
    await state.set_state(CopywriterStates.waiting_prompt)

    await callback_query.message.edit_text(
        uz.COPYWRITER_ASK_PROMPT.format(copy_type=type_name),
        parse_mode="HTML",
    )
    await callback_query.answer()


# ── Prompt handler ───────────────────────────
@router.message(CopywriterStates.waiting_prompt, F.text)
async def handle_copy_prompt(message: Message, state: FSMContext):
    """Generate copy using Gemini."""
    prompt = message.text.strip()

    # Skip menu buttons
    menu_buttons = [
        uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_CLUB,
        uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE,
    ]
    if prompt in menu_buttons:
        await state.clear()
        return

    data = await state.get_data()
    copy_type = data.get("copy_type", "Matn")
    copy_desc = data.get("copy_desc", "matn")

    # Spend tokens
    async with async_session() as session:
        if not await spend_tokens_async(session, message.from_user.id, COPY_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await state.clear()
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=COPY_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(user_id=message.from_user.id),
            )
            return
        await session.commit()

    status_msg = await message.answer(uz.COPYWRITER_GENERATING, parse_mode="HTML")

    try:
        # Build Gemini prompt
        gemini_prompt = (
            f"Sen professional kopirayter/kontent yozuvchisan. "
            f"O'zbek tilida {copy_desc} yoz.\n\n"
            f"Mavzu: {prompt}\n\n"
            f"Qoidalar:\n"
            f"- O'zbek tilida (lotin alifbosida) yoz\n"
            f"- Qisqa va ta'sirli bo'lsin\n"
            f"- Emoji ishlatishingiz mumkin\n"
            f"- Faqat tayyor matnni ber, izoh qo'shma\n"
            f"- {copy_type} formatida yoz"
        )

        logger.info(f"Calling Gemini for: {copy_type} - {prompt[:50]}")
        result = await asyncio.to_thread(_call_gemini, gemini_prompt)
        logger.info(f"Gemini response: {len(result)} chars")

        async with async_session() as session:
            tokens = await get_tokens_async(session, message.from_user.id)
        await status_msg.edit_text(
            uz.COPYWRITER_SUCCESS.format(text=result[:3500], tokens=tokens),
            parse_mode="HTML",
        )

        await state.clear()

        # Ask for another
        await message.answer(
            "Yana xizmat kerakmi? 👇",
            reply_markup=ai_workers_reply_keyboard(),
        )

        # Analytics
        try:
            from db.database import async_session
            from services.analytics import AnalyticsService
            from services.crm import CRMService
            async with async_session() as db:
                crm = CRMService(db)
                user = await crm.get_user(message.from_user.id)
                if user:
                    analytics = AnalyticsService(db)
                    await analytics.track(user_id=user.id, event_type="copywriter")
                    await db.commit()
        except Exception:
            pass

    except Exception as e:
        # Refund tokens on error
        async with async_session() as session:
            await add_tokens_async(session, message.from_user.id, COPY_COST)
            await session.commit()

        error_name = type(e).__name__
        error_msg = str(e)[:200]
        logger.error(f"Copywriter failed: {error_name}: {error_msg}")
        await state.clear()
        try:
            await status_msg.edit_text(
                f"❌ Xatolik: {error_name}: {error_msg}\n\n"
                f"Token qaytarildi. Qayta urinib ko'ring."
            )
        except Exception:
            await message.answer(uz.COPYWRITER_ERROR)
