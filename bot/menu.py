from bot.keyboards import main_menu_keyboard
from bot.profile import handle_profile
from bot.premium import handle_premium_menu
from bot.feedback import handle_feedback_start
from bot.workout import handle_plan_menu
from bot.languages import get_text
from core.db import db

def register_menu_handlers(bot):
    
    @bot.message_handler(func=lambda message: any(message.text == get_text("menu_profile", lang) for lang in ["uz", "ru", "en"]))
    def menu_profile(message):
        handle_profile(message, bot)

    @bot.message_handler(func=lambda message: any(message.text == get_text("menu_premium", lang) for lang in ["uz", "ru", "en"]))
    def menu_premium(message):
        handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: any(message.text == get_text("menu_plan", lang) for lang in ["uz", "ru", "en"]))
    def menu_plan(message):
        handle_plan_menu(message, bot)

    @bot.message_handler(func=lambda message: any(message.text == get_text("menu_feedback", lang) for lang in ["uz", "ru", "en"]))
    def menu_feedback(message):
        handle_feedback_start(message, bot)
        from bot.profile import handle_profile
        handle_profile(message, bot)
