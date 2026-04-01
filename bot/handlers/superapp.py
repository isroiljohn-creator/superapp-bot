"""Superapp menu handler — hub for extra bot features."""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.locales import uz
from bot.keyboards.buttons import superapp_keyboard

router = Router(name="superapp")


@router.message(F.text == uz.MENU_BTN_SUPERAPP)
async def menu_superapp(message: Message, state: FSMContext):
    """Show Superapp menu."""
    await state.clear()
    
    await message.answer(
        uz.SUPERAPP_MENU, 
        parse_mode="HTML", 
        reply_markup=superapp_keyboard()
    )

@router.message(F.text == uz.SUPERAPP_BTN_TEAM)
async def nuvi_team_fallback(message: Message):
    # Bu handler asosan fallback uchun xizmat qiladi, chunki web_app tugmasi 
    # to'g'ridan to'g'ri mini-app ni ochib yuboradi. Agar desktop/old version bo'lsa
    # shu yerga tushadi.
    from bot.config import settings
    
    # We ideally would check DB for is_team_member here, but since this is just a fallback,
    # we can allow it for admins and our specific user.
    if message.from_user.id in settings.ADMIN_IDS or message.from_user.id == 1392501306:
        await message.answer("💼 Nuvi Team ilovasini ochish uchun menyudagi tugmani bosing va Web App ga ruxsat bering.")
    else:
        await message.answer("Siz Nuvi jamoasi ro'yxatida yo'qsiz (yopiq).")

@router.callback_query(F.data == "superapp:back")
async def superapp_back(callback: CallbackQuery):
    """Back to superapp message block (closes it or asks to use keyboard)."""
    await callback.message.delete()
    await callback.answer("Yopildi", show_alert=False)
