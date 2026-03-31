"""AI Workers hub — sub-menu for Surat tayyorlash, Kopirayter, AI Chat, and Balance top-up.
Uses reply keyboard (not inline) for main navigation."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.locales import uz
from bot.config import settings
from bot.keyboards.buttons import get_main_menu, ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import (
    get_tokens_async, has_enough_async, claim_daily_async,
    add_tokens_async,
    IMAGE_COST, COPY_COST,
)

router = Router(name="ai_workers")
logger = logging.getLogger("ai_workers")


class TopupStates(StatesGroup):
    waiting_amount = State()


# ── Menu button handler ───────────────────────
@router.message(F.text == uz.MENU_BTN_AI_WORKERS)
async def menu_ai_workers(message: Message, state: FSMContext):
    """Show AI Workers sub-menu with reply keyboard."""
    await state.clear()

    await message.answer(
        "🤖 <b>AI hodimlar</b>\n\n"
        "Kechirasiz, hozirda bu menyu ishlab chiqish jarayonida.\n\n"
        "Tez orada sizga qulay AI hodimlarni taqdim qilamiz, "
        "biz bilan qolganingiz uchun rahmat! 🙏",
        parse_mode="HTML",
        reply_markup=await get_main_menu(message.from_user.id),
    )


# ── Image generation (keyboard button) ───────
@router.message(F.text == uz.AI_WORKERS_KB_IMAGE)
async def start_image_gen_kb(message: Message, state: FSMContext):
    """Start image generation from keyboard button."""
    async with async_session() as session:
        if not await has_enough_async(session, message.from_user.id, IMAGE_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=IMAGE_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=ai_workers_reply_keyboard(),
            )
            return

    from bot.handlers.imagegen import ImageGenStates
    await state.set_state(ImageGenStates.waiting_prompt)
    await message.answer(uz.IMAGEGEN_INTRO, parse_mode="HTML")


# ── Copywriter (keyboard button) ─────────────
@router.message(F.text == uz.AI_WORKERS_KB_COPY)
async def start_copywriter_kb(message: Message, state: FSMContext):
    """Start copywriter from keyboard button."""
    async with async_session() as session:
        if not await has_enough_async(session, message.from_user.id, COPY_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=COPY_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=ai_workers_reply_keyboard(),
            )
            return

    from bot.handlers.copywriter import copy_type_keyboard
    await message.answer(
        uz.COPYWRITER_INTRO,
        parse_mode="HTML",
        reply_markup=copy_type_keyboard(),
    )


# ── AI Chat (keyboard button) ────────────────
@router.message(F.text == uz.AI_WORKERS_KB_CHAT)
async def start_chat_kb(message: Message, state: FSMContext):
    """Start AI Chat from keyboard button."""
    from bot.handlers.chatbot import CHAT_COST
    async with async_session() as session:
        if not await has_enough_async(session, message.from_user.id, CHAT_COST):
            tokens = await get_tokens_async(session, message.from_user.id)
            await message.answer(
                uz.AI_WORKERS_NO_TOKENS.format(needed=CHAT_COST, have=tokens),
                parse_mode="HTML",
                reply_markup=ai_workers_reply_keyboard(),
            )
            return

    from bot.handlers.chatbot import ChatbotStates
    await state.set_state(ChatbotStates.chatting)
    await message.answer(
        "💬 <b>AI Chat</b>\n\n"
        "Menga istalgan savolni yozing — javob beraman!\n"
        "Har bir savol: 500 so'm\n\n"
        "✏️ Savolingizni yozing 👇",
        parse_mode="HTML",
    )


# ── Daily bonus (keyboard button) ────────────
@router.message(F.text == uz.AI_WORKERS_KB_DAILY)
async def daily_bonus_kb(message: Message):
    """Claim daily token bonus from keyboard button."""
    async with async_session() as session:
        success, tokens = await claim_daily_async(session, message.from_user.id)
        await session.commit()
    if success:
        await message.answer(
            uz.AI_WORKERS_DAILY_CLAIMED.format(tokens=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_reply_keyboard(),
        )
    else:
        await message.answer(
            uz.AI_WORKERS_DAILY_ALREADY.format(tokens=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_reply_keyboard(),
        )


# ── Legacy inline callbacks (backward compat) ─
@router.callback_query(F.data == "aiw:daily")
async def daily_bonus(callback_query: CallbackQuery):
    """Legacy: Claim daily token bonus via inline."""
    async with async_session() as session:
        success, tokens = await claim_daily_async(session, callback_query.from_user.id)
        await session.commit()
    text = uz.AI_WORKERS_DAILY_CLAIMED.format(tokens=tokens) if success else uz.AI_WORKERS_DAILY_ALREADY.format(tokens=tokens)
    await callback_query.message.edit_text(text, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data == "aiw:image")
async def start_image_gen(callback_query: CallbackQuery, state: FSMContext):
    """Legacy: Start image generation via inline."""
    async with async_session() as session:
        if not await has_enough_async(session, callback_query.from_user.id, IMAGE_COST):
            tokens = await get_tokens_async(session, callback_query.from_user.id)
            await callback_query.message.edit_text(
                uz.AI_WORKERS_NO_TOKENS.format(needed=IMAGE_COST, have=tokens),
                parse_mode="HTML",
            )
            await callback_query.answer()
            return
    from bot.handlers.imagegen import ImageGenStates
    await state.set_state(ImageGenStates.waiting_prompt)
    await callback_query.message.edit_text(uz.IMAGEGEN_INTRO, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data == "aiw:copy")
async def start_copywriter(callback_query: CallbackQuery, state: FSMContext):
    """Legacy: Start copywriter via inline."""
    async with async_session() as session:
        if not await has_enough_async(session, callback_query.from_user.id, COPY_COST):
            tokens = await get_tokens_async(session, callback_query.from_user.id)
            await callback_query.message.edit_text(
                uz.AI_WORKERS_NO_TOKENS.format(needed=COPY_COST, have=tokens),
                parse_mode="HTML",
            )
            await callback_query.answer()
            return
    from bot.handlers.copywriter import copy_type_keyboard
    await callback_query.message.edit_text(uz.COPYWRITER_INTRO, parse_mode="HTML", reply_markup=copy_type_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "aiw:back")
async def back_to_menu_inline(callback_query: CallbackQuery, state: FSMContext):
    """Legacy: Return to main menu via inline."""
    await state.clear()
    await callback_query.message.delete()
    await callback_query.bot.send_message(
        chat_id=callback_query.from_user.id,
        text=uz.MENU_TEXT,
        parse_mode="HTML",
        reply_markup=await get_main_menu(user_id=callback_query.from_user.id),
    )
    await callback_query.answer()


# ── Balance top-up (keyboard button) ─────────
@router.message(F.text == uz.AI_WORKERS_KB_TOPUP)
async def start_topup(message: Message, state: FSMContext):
    """Start balance top-up flow."""
    async with async_session() as session:
        tokens = await get_tokens_async(session, message.from_user.id)
    await state.set_state(TopupStates.waiting_amount)
    await message.answer(
        f"💰 <b>Balans to'ldirish</b>\n\n"
        f"Hozirgi balans: <b>{tokens:,} so'm</b>\n\n"
        f"Qancha to'ldirmoqchisiz? Summani so'mda yozing.\n"
        f"Minimal: 1,000 so'm\n\n"
        f"✏️ Summani yozing (masalan: 5000) 👇",
        parse_mode="HTML",
    )


@router.message(TopupStates.waiting_amount, F.text)
async def process_topup_amount(message: Message, state: FSMContext):
    """Process top-up amount."""
    raw_text = message.text.strip()

    # Exit on menu/back buttons (check BEFORE number parsing)
    exit_buttons = [
        uz.MENU_BTN_BACK, uz.AI_WORKERS_KB_BACK,
        uz.AI_WORKERS_KB_IMAGE, uz.AI_WORKERS_KB_COPY,
        uz.AI_WORKERS_KB_CHAT, uz.AI_WORKERS_KB_DAILY,
        uz.MENU_BTN_AI_WORKERS,
    ]
    if raw_text in exit_buttons:
        await state.clear()
        async with async_session() as session:
            tokens = await get_tokens_async(session, message.from_user.id)
        await message.answer(
            uz.AI_WORKERS_INTRO.format(tokens=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_reply_keyboard(),
        )
        return

    text = raw_text.replace(" ", "").replace(",", "")

    try:
        amount = int(text)
        if amount < 1000:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(
            "❌ Noto'g'ri summa. Minimal: 1,000 so'm\n"
            "Qayta yozing yoki 🔙 Orqaga bosing.",
        )
        return

    # Payment system is not yet enabled — inform the user
    await state.clear()
    await message.answer(
        "⚠️ <b>To'lov tizimi hali ulanmagan</b>\n\n"
        "Tez orada Click/Payme orqali to'ldirish imkoniyati qo'shiladi.\n"
        "Hozircha kunlik bonus orqali token oling! 🎁",
        parse_mode="HTML",
        reply_markup=ai_workers_reply_keyboard(),
    )

