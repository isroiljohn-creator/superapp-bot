from bot import onboarding, menu, gamification, admin, feedback, premium

def register_all_handlers(bot):
    onboarding.register_handlers(bot)
    menu.register_handlers(bot)
    gamification.register_handlers(bot)
    admin.register_handlers(bot)
    feedback.register_handlers(bot) # Implicitly handled via menu but good for future expansion if needed
    premium.register_handlers(bot)
    
    from bot import profile
    profile.register_handlers(bot)
