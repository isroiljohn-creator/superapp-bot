"""AI Chatbot handler — General Q&A via Gemini API."""
import logging
import json
import urllib.request
import asyncio

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.locales import uz
from bot.config import settings
from bot.keyboards.buttons import ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import (
    spend_tokens_async, get_tokens_async, add_tokens_async,
)

router = Router(name="chatbot")
logger = logging.getLogger("chatbot")

CHAT_COST = 500  # 500 so'm per message


class ChatbotStates(StatesGroup):
    chatting = State()


def _ask_gemini(prompt: str, history: list[dict] = None, system_prompt: str = None) -> str:
    """Call Gemini API for chat completion."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    default_system = (
        "Sen AI yordamchisan. O'zbek tilida javob ber. "
        "Qisqa, aniq va foydali javoblar ber. "
        "Savolga 2-3 paragrafda javob ber, kitob yozma."
    )
    system_text = system_prompt or default_system

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    # Build conversation
    contents = []
    if history:
        for msg in history[-6:]:  # Keep last 6 messages for context
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["text"]}]
            })
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    payload = json.dumps({
        "contents": contents,
        "system_instruction": {
            "parts": [{"text": system_text}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
    })

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    candidates = data.get("candidates", [])
    if candidates and candidates[0].get("content", {}).get("parts"):
        return candidates[0]["content"]["parts"][0]["text"]
    raise ValueError("Gemini javob bermadi")


@router.message(ChatbotStates.chatting, F.text)
async def handle_chat_message(message: Message, state: FSMContext):
    """Handle user message in chat mode."""
    text = message.text.strip()

    # Exit on menu buttons
    menu_buttons = [
        uz.MENU_BTN_AI_WORKERS, uz.MENU_BTN_FREE_LESSONS, uz.MENU_BTN_CLUB,
        uz.MENU_BTN_COURSE, uz.MENU_BTN_PROFILE, uz.MENU_BTN_BACK,
        uz.AI_WORKERS_KB_IMAGE, uz.AI_WORKERS_KB_COPY, uz.AI_WORKERS_KB_DAILY,
        uz.AI_WORKERS_KB_CHAT, uz.AI_WORKERS_KB_TOPUP, uz.AI_WORKERS_KB_BACK,
        uz.AI_WORKERS_KB_PRES, uz.AI_WORKERS_KB_LYRICS,
    ]
    if text in menu_buttons:
        await state.clear()
        if text in {uz.MENU_BTN_BACK, uz.AI_WORKERS_KB_BACK}:
            from bot.keyboards.buttons import get_main_menu
            await message.answer(uz.MENU_TEXT, reply_markup=await get_main_menu(user_id=message.from_user.id), parse_mode="HTML")
        elif text == uz.MENU_BTN_AI_WORKERS:
            from db.database import async_session
            from services.token_service import get_tokens_async
            from bot.keyboards.buttons import ai_workers_reply_keyboard
            async with async_session() as session:
                tokens = await get_tokens_async(session, message.from_user.id)
            await message.answer(uz.AI_WORKERS_INTRO.format(tokens=tokens), parse_mode="HTML", reply_markup=ai_workers_reply_keyboard())
        return

    # Spend tokens
    async with async_session() as session:
        if not await spend_tokens_async(session, message.from_user.id, CHAT_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await state.clear()
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=CHAT_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=ai_workers_reply_keyboard(),
            )
            return
        await session.commit()

    status_msg = await message.answer("💬 Javob tayyorlanmoqda... ⏳")

    try:
        # Get conversation history from FSM
        data = await state.get_data()
        history = data.get("chat_history", [])

        # Call Gemini with custom prompt from DB
        custom_prompt = None
        try:
            from db.models import AdminSetting
            from sqlalchemy import select
            async with async_session() as db:
                r = await db.execute(select(AdminSetting.value).where(AdminSetting.key == "prompt_chatbot"))
                custom_prompt = r.scalar_one_or_none()
        except Exception:
            pass
        response = await asyncio.to_thread(_ask_gemini, text, history, custom_prompt)

        # Save to history
        history.append({"role": "user", "text": text})
        history.append({"role": "model", "text": response})
        await state.update_data(chat_history=history[-10:])  # keep last 10

        # Show response
        async with async_session() as session:
            tokens = await get_tokens_async(session, message.from_user.id)

        try:
            await status_msg.delete()
        except Exception:
            pass

        # HTML-escape Gemini response to prevent injection
        import html as html_mod
        safe_response = html_mod.escape(response)

        await message.answer(
            f"{safe_response}\n\n💰 <i>Qolgan balans: {tokens:,} so'm</i>",
            parse_mode="HTML",
        )

    except Exception as e:
        # Refund on error
        async with async_session() as session:
            await add_tokens_async(session, message.from_user.id, CHAT_COST)
            await session.commit()
        logger.error(f"Chatbot error: {type(e).__name__}: {e}")
        await state.clear()
        try:
            await status_msg.edit_text(
                f"❌ Xatolik: {type(e).__name__}\nBalans qaytarildi. Qayta urinib ko'ring."
            )
        except Exception:
            pass
