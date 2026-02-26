"""Main menu handler — responds to menu button presses."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.keyboards.buttons import main_menu_keyboard, subscribe_keyboard
from bot.locales import uz
from bot.config import settings

router = Router(name="menu")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu."""
    await message.answer(uz.MENU_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.message(F.text == uz.MENU_BTN_CLUB)
async def menu_club(message: Message):
    """Yopiq klub section."""
    await message.answer(
        uz.CLUB_TEXT.format(price=f"{settings.CLUB_PRICE:,}"),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == uz.MENU_BTN_COURSE)
async def menu_course(message: Message):
    """Nuvi kursi section."""
    await message.answer(
        uz.COURSE_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == uz.MENU_BTN_LESSONS)
async def menu_lessons(message: Message):
    """Darslar section."""
    await message.answer(
        uz.LESSONS_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == uz.MENU_BTN_GUIDES)
async def menu_guides(message: Message):
    """Qo'llanmalar section."""
    await message.answer(
        uz.GUIDES_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == uz.MENU_BTN_HELP)
async def menu_help(message: Message):
    """Yordam section."""
    await message.answer(uz.HELP_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard())


@router.message(F.text == uz.MENU_BTN_SETTINGS)
async def menu_settings(message: Message):
    """Sozlama section."""
    await message.answer(uz.SETTINGS_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard())
