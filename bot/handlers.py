from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates

def register_all_handlers(bot):
    # EMERGENCY PROFILE HANDLER - High Priority
    @bot.message_handler(func=lambda message: "Profil" in message.text)
    def emergency_profile_handler(message):
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
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        print(f"DEBUG: /start command received from {message.from_user.id}")
        # Always start with onboarding (which now asks for language first)
        try:
            onboarding.start_onboarding(message, bot)
        except Exception as e:
            print(f"ERROR in handle_start: {e}")
            import traceback
            traceback.print_exc()
            bot.reply_to(message, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")

    @bot.message_handler(commands=['language', 'lang'])
    def handle_language(message):
        user_id = message.from_user.id
        # Reset to language selection state
        onboarding.manager.set_state(user_id, onboarding.STATE_LANGUAGE)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🇺🇿 O'zbekcha", "🇷🇺 Русский", "🇬🇧 English")
        
        bot.send_message(user_id, "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык / 🇬🇧 Select language", reply_markup=markup)

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
            
        # Restart onboarding
        onboarding.start_onboarding(message, bot)

    @bot.message_handler(commands=['version'])
    def handle_version(message):
        bot.reply_to(message, "🤖 Bot Version: v2.6 - Multi-language Support")

    # Debug callback LAST (as fallback)
    @bot.callback_query_handler(func=lambda call: True)
    def debug_callback(call):
        print(f"DEBUG: Unhandled callback: {call.data} from {call.from_user.id}")
        bot.answer_callback_query(call.id, "⚠️ Bu tugma hali ishlamayapti")
        
    # Debug message handler (catch-all for debugging)
    @bot.message_handler(func=lambda m: True)
    def debug_message(message):
        # Ignore if it matches any known button text in any language
        # This is expensive but safe for now
        # Actually, if we are here, it means no other handler caught it.
        # But we have localized handlers in menu.py that check for specific texts.
        # If we are here, it's truly unhandled.
        
        print(f"DEBUG: Unhandled message: {message.text} from {message.from_user.id}")
        # Only reply if it looks like a command or button press failed
        if message.text.startswith("/") or message.text in ["👤 Profil", "Profil"]:
             bot.reply_to(message, f"⚠️ DEBUG: Men '{message.text}' xabarini oldim, lekin unga javob beradigan handler topilmadi.\n\nIltimos /start ni bosing.")

