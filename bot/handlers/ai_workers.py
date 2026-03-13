"""AI Workers hub — sub-menu for Surat tayyorlash and Kopirayter.
Uses reply keyboard (not inline) for main navigation."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.locales import uz
from bot.keyboards.buttons import main_menu_keyboard, ai_workers_reply_keyboard
from db.database import async_session
from services.token_service import (
    get_tokens_async, has_enough_async, claim_daily_async,
    IMAGE_COST, COPY_COST,
)

router = Router(name="ai_workers")
logger = logging.getLogger("ai_workers")


# ── Menu button handler ───────────────────────
@router.message(F.text == uz.MENU_BTN_AI_WORKERS)
async def menu_ai_workers(message: Message, state: FSMContext):
    """Show AI Workers sub-menu with reply keyboard."""
    await state.clear()
    async with async_session() as session:
        tokens = await get_tokens_async(session, message.from_user.id)
    await message.answer(
        uz.AI_WORKERS_INTRO.format(tokens=tokens),
        parse_mode="HTML",
        reply_markup=ai_workers_reply_keyboard(),
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
        reply_markup=main_menu_keyboard(user_id=callback_query.from_user.id),
    )
    await callback_query.answer()
