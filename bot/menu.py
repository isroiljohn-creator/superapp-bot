from bot.workout import handle_workout_plan, handle_meal_plan
from bot.referral import handle_referral
from bot.gamification import handle_tasks
from bot.keyboards import main_menu_keyboard
from bot.feedback import handle_feedback_start
from bot.premium import handle_premium_menu

def register_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == "Mening rejam 📅")
    def menu_workout(message):
        handle_workout_plan(message, bot)

    @bot.message_handler(func=lambda message: message.text == "Menyu 🍏")
    def menu_meal(message):
        handle_meal_plan(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔗 Referal")
    def menu_referral(message):
        handle_referral(message, bot)

    @bot.message_handler(func=lambda message: message.text == "Vazifalar ✅")
    def menu_tasks(message):
        handle_tasks(message, bot)

    @bot.message_handler(func=lambda message: message.text == "💎 Premium")
    def menu_premium(message):
        handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📞 Qayta aloqa")
    def menu_feedback(message):
        handle_feedback_start(message, bot)

    @bot.message_handler(func=lambda message: "Profil" in message.text)
    def menu_profile(message):
        print(f"DEBUG: Menu Profile button clicked by {message.from_user.id}")
        from bot.profile import handle_profile
        handle_profile(message, bot)
