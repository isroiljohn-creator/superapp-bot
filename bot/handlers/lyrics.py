"""Lyrics generator — AI-powered song/poetry writing via Gemini."""
import asyncio
import json
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import settings
from bot.locales import uz
from bot.keyboards.buttons import ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import (
    get_tokens_async, has_enough_async, spend_tokens_async, add_tokens_async,
    LYRICS_COST,
)

router = Router(name="lyrics")
logger = logging.getLogger("lyrics")


class LyricsStates(StatesGroup):
    waiting_type = State()
    waiting_prompt = State()


LYRICS_TYPES = {
    "pop": ("🎤 Pop qo'shiq", "pop musiqasi uchun qo'shiq matni"),
    "rap": ("🎙️ Rap", "rap qo'shiq matni (ritmik, qofiyali)"),
    "romantic": ("❤️ Romantik", "romantik sevgi qo'shig'i matni"),
    "folk": ("🪕 Xalq qo'shig'i", "o'zbek xalq qo'shig'i uslubida matn"),
    "poem": ("📜 She'r", "go'zal she'r (qofiyali)"),
    "nasheed": ("🌙 Nashid", "nashid (ilohiy qo'shiq) matni"),
}


def _lyrics_type_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, (label, _) in LYRICS_TYPES.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"lyrics_type:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


LYRICS_SYSTEM_PROMPT = (
    "Sen professional qo'shiq matni va she'r yozuvchisan. "
    "O'zbek tilida (lotin alifbosida) yozasan.\n\n"
    "Qoidalar:\n"
    "- Matn go'zal, ta'sirli va qofiyali bo'lsin\n"
    "- 3-4 ta kuplet + naqorat yoz\n"
    "- Faqat tayyor qo'shiq matnini ber, izoh yoki boshqa narsa qo'shma\n"
    "- Har bir kupletni [Kuplet 1], [Kuplet 2] deb belgilab yoz\n"
    "- Naqoratni [Naqorat] deb belgilab yoz\n"
    "- So'ngida muallif deb 'AI Lyrics — Nuvi Academy Bot' yoz"
)


def _call_gemini(prompt: str, lyrics_type_desc: str) -> str:
    """Call Gemini API for lyrics."""
    import urllib.request
    api_key = settings.GEMINI_API_KEY
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    full_prompt = f"{lyrics_type_desc}\n\nMavzu: {prompt}"

    body = json.dumps({
        "system_instruction": {"parts": [{"text": LYRICS_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2048},
    }).encode()

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())

    return data["candidates"][0]["content"]["parts"][0]["text"]


@router.message(F.text == uz.AI_WORKERS_KB_LYRICS)
async def start_lyrics(message: Message, state: FSMContext):
    """Start lyrics generation flow — choose type."""
    async with async_session() as session:
        if not await has_enough_async(session, message.from_user.id, LYRICS_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=LYRICS_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=ai_workers_reply_keyboard(),
            )
            return

    await message.answer(uz.LYRICS_INTRO, parse_mode="HTML", reply_markup=_lyrics_type_keyboard())
    await state.set_state(LyricsStates.waiting_type)


@router.callback_query(LyricsStates.waiting_type, F.data.startswith("lyrics_type:"))
async def process_lyrics_type(callback: CallbackQuery, state: FSMContext):
    """Save lyrics type, ask for topic."""
    lyrics_key = callback.data.split(":")[1]
    if lyrics_key not in LYRICS_TYPES:
        await callback.answer("Noto'g'ri tur")
        return

    label, desc = LYRICS_TYPES[lyrics_key]
    await state.update_data(lyrics_type=lyrics_key, lyrics_desc=desc, lyrics_label=label)
    await callback.message.edit_text(
        uz.LYRICS_ASK_PROMPT.format(lyrics_type=label),
        parse_mode="HTML",
    )
    await state.set_state(LyricsStates.waiting_prompt)
    await callback.answer()


@router.message(LyricsStates.waiting_prompt, F.text)
async def handle_lyrics_prompt(message: Message, state: FSMContext):
    """Generate lyrics from prompt."""
    prompt = message.text.strip()

    # Check for menu buttons
    menu_buttons = [
        uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_CLUB,
        uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE, uz.MENU_BTN_BACK,
        uz.AI_WORKERS_KB_IMAGE, uz.AI_WORKERS_KB_COPY, uz.AI_WORKERS_KB_CHAT,
        uz.AI_WORKERS_KB_DAILY, uz.AI_WORKERS_KB_TOPUP, uz.AI_WORKERS_KB_BACK,
        uz.AI_WORKERS_KB_PRES, uz.AI_WORKERS_KB_LYRICS,
    ]
    if prompt in menu_buttons:
        await state.clear()
        return

    data = await state.get_data()
    lyrics_desc = data.get("lyrics_desc", "qo'shiq matni")
    lyrics_label = data.get("lyrics_label", "🎵 Qo'shiq")

    # Spend tokens
    async with async_session() as session:
        if not await spend_tokens_async(session, message.from_user.id, LYRICS_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await state.clear()
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=LYRICS_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=ai_workers_reply_keyboard(),
            )
            return
        await session.commit()

    status_msg = await message.answer(uz.LYRICS_GENERATING, parse_mode="HTML")

    try:
        result = await asyncio.to_thread(_call_gemini, prompt, lyrics_desc)

        async with async_session() as session:
            tokens = await get_tokens_async(session, message.from_user.id)

        try:
            await status_msg.delete()
        except Exception:
            pass

        # HTML-escape the result
        import html as html_mod
        safe_result = html_mod.escape(result)

        await message.answer(
            f"🎵 <b>{lyrics_label} tayyor!</b>\n\n"
            f"{safe_result}\n\n"
            f"💰 Qolgan balans: {tokens:,} so'm",
            parse_mode="HTML",
            reply_markup=ai_workers_reply_keyboard(),
        )

        # Track analytics
        try:
            async with async_session() as session:
                from services.analytics import AnalyticsService
                from services.crm import CRMService
                crm = CRMService(session)
                user = await crm.get_user(message.from_user.id)
                if user:
                    analytics = AnalyticsService(session)
                    await analytics.track(user_id=user.id, event_type="lyrics")
                    await session.commit()
        except Exception:
            pass

    except Exception as e:
        # Refund on error
        async with async_session() as session:
            await add_tokens_async(session, message.from_user.id, LYRICS_COST)
            await session.commit()
        logger.error(f"Lyrics error: {type(e).__name__}: {e}")
        try:
            await status_msg.edit_text(uz.LYRICS_ERROR)
        except Exception:
            pass

    await state.clear()
