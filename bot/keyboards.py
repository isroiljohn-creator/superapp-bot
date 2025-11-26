from telebot import types
from bot.languages import get_text
import os
from telebot.types import WebAppInfo

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://google.com")

def phone_request_keyboard():
    """Request phone number from user"""
    markup.add(
        KeyboardButton("Mening rejam 📅"),
        KeyboardButton("Menyu 🍏")
    )
    markup.add(
        KeyboardButton("Vazifalar ✅"),
        KeyboardButton("👤 Profil")
    )
    markup.add(
        KeyboardButton("💎 Premium"),
        KeyboardButton("📞 Qayta aloqa")
    )
    markup.add(KeyboardButton("🔗 Referal"))
    return markup

def gamification_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Mashq qildim ✅", callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton("Suv ichdim 💧", callback_data="daily_water_done"))
    return markup
