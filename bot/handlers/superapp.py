"""Superapp menu handler — hub for extra bot features."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales import uz
from bot.keyboards.buttons import main_menu_keyboard

router = Router(name="superapp")


@router.message(F.text == uz.MENU_BTN_SUPERAPP)
async def menu_superapp(message: Message, state: FSMContext):
    """Show Superapp menu."""
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Nazoratchi bot", callback_data="superapp:moderator")],
    ])
    await message.answer(uz.SUPERAPP_MENU, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "superapp:back")
async def superapp_back(callback: CallbackQuery):
    """Back to superapp menu."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Nazoratchi bot", callback_data="superapp:moderator")],
    ])
    await callback.message.edit_text(uz.SUPERAPP_MENU, parse_mode="HTML", reply_markup=kb)
    await callback.answer()
