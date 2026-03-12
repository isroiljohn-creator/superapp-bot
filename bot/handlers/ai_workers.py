"""AI Workers hub — sub-menu for Surat tayyorlash and Kopirayter."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from bot.locales import uz
from bot.keyboards.buttons import main_menu_keyboard
from services.token_service import get_tokens, claim_daily, has_enough, IMAGE_COST, COPY_COST

router = Router(name="ai_workers")
logger = logging.getLogger("ai_workers")


def ai_workers_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    """AI Workers sub-menu with token balance."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=uz.AI_WORKERS_BTN_IMAGE, callback_data="aiw:image")],
        [InlineKeyboardButton(text=uz.AI_WORKERS_BTN_COPY, callback_data="aiw:copy")],
        [InlineKeyboardButton(text=uz.AI_WORKERS_BTN_DAILY, callback_data="aiw:daily")],
        [InlineKeyboardButton(text=uz.AI_WORKERS_BTN_BACK, callback_data="aiw:back")],
    ])


# ── Menu button handler ───────────────────────
@router.message(F.text == uz.MENU_BTN_AI_WORKERS)
async def menu_ai_workers(message: Message, state: FSMContext):
    """Show AI Workers sub-menu."""
    await state.clear()
    tokens = get_tokens(message.from_user.id)
    await message.answer(
        uz.AI_WORKERS_INTRO.format(tokens=tokens),
        parse_mode="HTML",
        reply_markup=ai_workers_keyboard(message.from_user.id),
    )


# ── Daily bonus ──────────────────────────────
@router.callback_query(F.data == "aiw:daily")
async def daily_bonus(callback_query: CallbackQuery):
    """Claim daily token bonus."""
    success, tokens = claim_daily(callback_query.from_user.id)
    if success:
        await callback_query.message.edit_text(
            uz.AI_WORKERS_DAILY_CLAIMED.format(tokens=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_keyboard(callback_query.from_user.id),
        )
    else:
        await callback_query.message.edit_text(
            uz.AI_WORKERS_DAILY_ALREADY.format(tokens=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_keyboard(callback_query.from_user.id),
        )
    await callback_query.answer()


# ── Image generation ─────────────────────────
@router.callback_query(F.data == "aiw:image")
async def start_image_gen(callback_query: CallbackQuery, state: FSMContext):
    """Start image generation — check tokens first."""
    if not has_enough(callback_query.from_user.id, IMAGE_COST):
        tokens = get_tokens(callback_query.from_user.id)
        await callback_query.message.edit_text(
            uz.AI_WORKERS_NO_TOKENS.format(needed=IMAGE_COST, have=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_keyboard(callback_query.from_user.id),
        )
        await callback_query.answer()
        return

    # Import and trigger imagegen FSM
    from bot.handlers.imagegen import ImageGenStates
    await state.set_state(ImageGenStates.waiting_prompt)
    await callback_query.message.edit_text(
        uz.IMAGEGEN_INTRO,
        parse_mode="HTML",
    )
    await callback_query.answer()


# ── Copywriter ───────────────────────────────
@router.callback_query(F.data == "aiw:copy")
async def start_copywriter(callback_query: CallbackQuery, state: FSMContext):
    """Start copywriter — check tokens first."""
    if not has_enough(callback_query.from_user.id, COPY_COST):
        tokens = get_tokens(callback_query.from_user.id)
        await callback_query.message.edit_text(
            uz.AI_WORKERS_NO_TOKENS.format(needed=COPY_COST, have=tokens),
            parse_mode="HTML",
            reply_markup=ai_workers_keyboard(callback_query.from_user.id),
        )
        await callback_query.answer()
        return

    # Show copy type selection
    from bot.handlers.copywriter import copy_type_keyboard
    await callback_query.message.edit_text(
        uz.COPYWRITER_INTRO,
        parse_mode="HTML",
        reply_markup=copy_type_keyboard(),
    )
    await callback_query.answer()


# ── Back to menu ─────────────────────────────
@router.callback_query(F.data == "aiw:back")
async def back_to_menu(callback_query: CallbackQuery, state: FSMContext):
    """Return to main menu."""
    await state.clear()
    await callback_query.message.delete()
    await callback_query.message.answer(
        uz.MENU_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(user_id=callback_query.from_user.id),
    )
    await callback_query.answer()
