from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates
from bot.calories import handle_calorie_button, handle_food_photo, STATE_CALORIE_PHOTO
from bot.keyboards import main_menu_keyboard

def register_all_handlers(bot):
    # Calorie Handlers
    @bot.message_handler(func=lambda message: message.text == "📸 Kaloriyani aniqlash")
    def calorie_handler(message):
        handle_calorie_button(message, bot, onboarding.manager)

    @bot.message_handler(content_types=['photo'])
    def photo_handler(message):
        if onboarding.manager.get_state(message.from_user.id) == STATE_CALORIE_PHOTO:
            handle_food_photo(message, bot, onboarding.manager)

    # EMERGENCY PROFILE HANDLER - High Priority
            
    @bot.message_handler(func=lambda message: message.text == "👤 Profil")
    def profile_handler(message):
        print(f"DEBUG: EMERGENCY PROFILE HANDLER triggered by {message.from_user.id}")
        from bot.profile import handle_profile
        handle_profile(message, bot)

    @bot.message_handler(commands=['profile_debug'])
    def debug_profile_command(message):
        print(f"DEBUG: /profile_debug triggered")
        from bot.profile import handle_profile
        handle_profile(message, bot)

    # Register all module handlers
    onboarding.register_handlers(bot)
    menu.register_handlers(bot)
    gamification.register_handlers(bot)
    admin.register_handlers(bot)
    feedback.register_handlers(bot)
    premium.register_handlers(bot)
    profile.register_handlers(bot)
    templates.register_handlers(bot)
    
    # General utility handlers
    @bot.message_handler(commands=['menu'])
    def handle_menu_command(message):
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_keyboard())

    @bot.message_handler(commands=['ping'])
    def handle_ping(message):
        bot.reply_to(message, "Pong! 🏓 Bot ishlamoqda.")

    @bot.message_handler(commands=['myid'])
    def handle_myid(message):
        bot.reply_to(message, f"🆔 Sizning ID raqamingiz: `{message.from_user.id}`", parse_mode="Markdown")

    @bot.message_handler(commands=['reset'])
    def handle_reset(message):
        """Force reset user state"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Clear onboarding state
        onboarding.manager.clear_user(user_id)
        
        # Clear Telebot next step handlers (CRITICAL FIX)
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
        except Exception as e:
            print(f"Error clearing step handler: {e}")
            
        bot.reply_to(message, "🔄 Holat to'liq tozalandi (Step Handlers + State). /start ni bosing.")

    @bot.message_handler(commands=['version'])
    def handle_version(message):
        bot.reply_to(message, "🤖 Bot Version: v2.5 - DEBUG MODE\n\nAgar bu xabarni ko'rayotgan bo'lsangiz, demak bot yangilangan!")

    # Debug callback LAST (as fallback)
    @bot.callback_query_handler(func=lambda call: True)
    def debug_callback(call):
        print(f"DEBUG: Unhandled callback: {call.data} from {call.from_user.id}")
        bot.answer_callback_query(call.id, "⚠️ Bu tugma hali ishlamayapti")
        
    # Debug message handler (catch-all for debugging)
    @bot.message_handler(func=lambda m: True)
    def debug_message(message):
        print(f"DEBUG: Unhandled message: {message.text} from {message.from_user.id}")
        # Only reply if it looks like a command or button press failed
        if message.text.startswith("/") or message.text in ["👤 Profil", "Profil"]:
             bot.reply_to(message, f"⚠️ DEBUG: Men '{message.text}' xabarini oldim, lekin unga javob beradigan handler topilmadi.\n\nIltimos /reset ni bosing.")

