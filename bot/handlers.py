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
        # Clear onboarding state
        onboarding.manager.clear_user(user_id)
        bot.reply_to(message, "🔄 Holat tozalandi. /start ni bosing.")

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

