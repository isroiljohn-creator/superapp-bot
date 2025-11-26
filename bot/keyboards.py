from telebot import types
from bot.languages import get_text
import os
from telebot.types import WebAppInfo

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://google.com")

def phone_request_keyboard(lang="uz"):
    """Request phone number from user"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Phone", request_contact=True))
    return markup

def main_menu_keyboard(lang="uz"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(get_text("menu_plan", lang)),
        types.KeyboardButton(get_text("menu_profile", lang)),
        types.KeyboardButton(get_text("menu_premium", lang)),
        types.KeyboardButton(get_text("menu_progress", lang)),
        types.KeyboardButton(get_text("menu_feedback", lang)),
        types.KeyboardButton(get_text("menu_settings", lang))
    )
    return markup

def gender_keyboard(lang="uz"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(get_text("male", lang)),
        types.KeyboardButton(get_text("female", lang))
    )
    return markup

def goal_keyboard(lang="uz"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(get_text("goal_weight_loss", lang)),
        types.KeyboardButton(get_text("goal_mass_gain", lang))
    )
    markup.add(types.KeyboardButton(get_text("goal_health", lang)))
    return markup

def allergy_keyboard(lang="uz"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(get_text("no", lang)),
        types.KeyboardButton(get_text("yes", lang))
    )
    return markup
