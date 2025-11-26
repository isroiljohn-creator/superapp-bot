from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates

def register_all_handlers(bot):
    @bot.message_handler(commands=['ping'])
    def handle_ping(message):
        bot.reply_to(message, "Pong! 🏓 Bot ishlamoqda.")

    @bot.message_handler(commands=['myid'])
    def handle_myid(message):
        bot.reply_to(message, f"🆔 Sizning ID raqamingiz: `{message.from_user.id}`", parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: True, pass_through=True)
    def debug_callback(call):
        print(f"DEBUG: Callback received: {call.data} from {call.from_user.id}")
        return False # Continue to other handlers

    onboarding.register_handlers(bot)
    menu.register_handlers(bot)
    gamification.register_handlers(bot)
    admin.register_handlers(bot)
    feedback.register_handlers(bot) # Implicitly handled via menu but good for future expansion if needed
    premium.register_handlers(bot)
    profile.register_handlers(bot)
    templates.register_handlers(bot)  # NEW: Template plan handlers
