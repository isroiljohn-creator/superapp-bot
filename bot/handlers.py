from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates, workout
from bot.calories import handle_calorie_button, handle_food_photo, STATE_CALORIE_PHOTO
from bot.languages import get_text, TRANS
from bot.keyboards import (
    main_menu_keyboard, plan_inline_keyboard, habits_inline_keyboard, 
    ai_inline_keyboard, points_inline_keyboard, challenges_inline_keyboard,
    profile_inline_keyboard, premium_inline_keyboard
)
from bot import trackers, ai_features, challenges, calorie_scanner

from core.db import db

def register_all_handlers(bot):
    # --- Global Logging Middleware ---
    def log_middleware(bot_instance, update):
        try:
            user_id = None
            content = ""
            type_ = ""
            
            if hasattr(update, 'message') and update.message:
                # CallbackQuery
                user_id = update.from_user.id
                content = f"Callback: {update.data}"
                type_ = "callback"
            elif hasattr(update, 'text'):
                # Message
                user_id = update.from_user.id
                content = update.text
                type_ = "message"
            
            if user_id:
                db.log_activity(user_id, type_, content)
        except Exception as e:
            print(f"Logging Error: {e}")

    # Register middleware manually if supported or use a catch-all check
    # Telebot middleware is a bit specific. Let's use a simple pre-execution hook if possible.
    # Or better, just use a handler that matches everything but doesn't stop propagation?
    # Telebot handlers stop propagation if they handle it.
    # Best way in standard telebot is `bot.register_middleware_handler(log_middleware, update_types=['message', 'callback_query'])`
    try:
        bot.register_middleware_handler(log_middleware, update_types=['message', 'callback_query'])
    except AttributeError:
        # Fallback for older versions or if method missing
        print("Warning: register_middleware_handler not found. Logging might be limited.")
# Helper to find key by value (reverse lookup)
def get_key_by_text(text):
    for lang in TRANS:
        for key, value in TRANS[lang].items():
            if value == text:
                return key
    return None

    # --- Main Menu Navigation & Global Handlers ---
    


    # --- Sub-Menu Handlers ---

    # --- Photo Handler ---
    @bot.message_handler(content_types=['photo'])
    def photo_handler(message):
        # Check for calorie scanner state
        state = onboarding.manager.get_state(message.from_user.id)
        if state == calorie_scanner.STATE_CALORIE_PHOTO:
            calorie_scanner.handle_calorie_photo(message, bot)
            return
        pass

    # Register module handlers (callbacks etc)
    onboarding.register_handlers(bot)
    menu.register_handlers(bot)
    gamification.register_handlers(bot)
    admin.register_handlers(bot)
    feedback.register_handlers(bot)
    premium.register_handlers(bot)
    profile.register_handlers(bot)
    templates.register_handlers(bot)

    # --- Callbacks ---
    
    # Tracker Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('track_'))
    def tracker_action_callback(call):
        type = call.data.split('_')[1]
        if type == 'water': trackers.process_water_callback(call, bot)
        elif type == 'mood': trackers.process_mood_callback(call, bot)
        # Sleep is now input based, but we might have old buttons or need to remove them?
        # The new tracker uses input for sleep, so no callback needed for sleep logic unless we kept buttons.
        # But wait, handle_sleep_tracker in trackers.py now asks for input, so no buttons.
        # So we can remove sleep callback here.

    # AI Tool Callbacks (if any left using callbacks)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('ai_tool_'))
    def ai_tool_callback(call):
        tool = call.data.split('_')[2]
        if tool == 'shopping': ai_features.handle_shopping_list(call.message, bot)
        elif tool == 'recipe': ai_features.handle_recipe_gen(call.message, bot)
        elif tool == 'report': ai_features.handle_weekly_report(call.message, bot)
        bot.answer_callback_query(call.id)

    # Challenge Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('challenge_'))
    def challenge_callback(call):
        action = call.data.replace('challenge_', '')
        if action == 'daily': challenges.handle_daily_challenge(call, bot)
        elif action == 'leaderboard': challenges.show_leaderboard(call, bot)
        elif action == 'complete': 
            challenges.complete_challenge(call, bot, 10)
        elif action == 'weekly': challenges.handle_weekly_challenge(call.message, bot)
        elif action == 'monthly': challenges.handle_monthly_challenge(call.message, bot)
        elif action == 'friends': challenges.handle_friends_challenge(call.message, bot)
        bot.answer_callback_query(call.id)

    # Calorie Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('calorie_mode_'))
    def calorie_mode_handler(call):
        calorie_scanner.calorie_mode_callback(call, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == calorie_scanner.STATE_CALORIE_TEXT)
    def text_calorie_handler(message):
        calorie_scanner.handle_calorie_text(message, bot)

    # --- Inline Menu Callbacks ---

    # Plan Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('plan_'))
    def plan_callback(call):
        action = call.data.replace('plan_', '')
        if action == 'ai_workout': workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
        elif action == 'ai_meal': workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)
        elif action == 'calorie_scan': calorie_scanner.show_calorie_menu(call.message, bot)
        bot.answer_callback_query(call.id)

    # Habits Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('habit_'))
    def habit_callback(call):
        action = call.data.replace('habit_', '')
        if action == 'water': trackers.handle_water_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'sleep': trackers.handle_sleep_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'mood': trackers.handle_mood_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'steps': trackers.handle_steps_tracker(call.message, bot, user_id=call.from_user.id)
        elif action == 'stats': trackers.handle_habits_stats(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # AI Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('ai_'))
    def ai_callback(call):
        action = call.data.replace('ai_', '')
        # Handle ai_tool_ prefix from old callbacks if any, but we renamed to ai_
        if action == 'qa': ai_features.handle_ai_qa(call.message, bot)
        elif action == 'meal': workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)
        elif action == 'workout': workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
        elif action == 'recipe': ai_features.handle_recipe_gen(call.message, bot)
        elif action == 'shopping': ai_features.handle_shopping_list(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Points Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('points_'))
    def points_callback(call):
        action = call.data.replace('points_', '')
        if action == 'balance': gamification.handle_my_points(call.message, bot, user_id=call.from_user.id)
        elif action == 'rewards': gamification.handle_rewards(call.message, bot)
        elif action == 'rules': gamification.handle_rules(call.message, bot)
        elif action == 'referral': gamification.handle_referral_link(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Challenges Callbacks (Merged with existing if needed, but existing uses challenge_ prefix too)
    # Existing handler handles: daily, leaderboard, complete.
    # We added: weekly, monthly, friends, leaderboard.
    # Let's update the existing handler or add new logic.
    # Existing handler is at line 192. I will replace it or merge.
    # I'll replace the existing challenge callback handler to include new menu items.

    # Profile Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('profile_'))
    def profile_callback(call):
        action = call.data.replace('profile_', '')
        if action == 'edit': profile.handle_edit_profile_command(call.message, bot)
        elif action == 'stats': profile.handle_profile_stats(call.message, bot, user_id=call.from_user.id)
        elif action == 'change_goal': profile.handle_change_goal_command(call.message, bot)
        bot.answer_callback_query(call.id)

    # Premium Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('premium_'))
    def premium_callback(call):
        action = call.data.replace('premium_', '')
        if action == 'buy': premium.handle_premium_buy(call.message, bot)
        elif action == 'info': premium.handle_premium_info(call.message, bot)
        elif action == 'coins': gamification.handle_points_menu(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

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
        user_id = message.from_user.id
        chat_id = message.chat.id
        onboarding.manager.clear_user(user_id)
        try:
            bot.clear_step_handler_by_chat_id(chat_id)
        except Exception as e:
            print(f"Error clearing step handler: {e}")
        bot.reply_to(message, "🔄 Holat to'liq tozalandi. /start ni bosing.")

    @bot.message_handler(commands=['version'])
    def handle_version(message):
        bot.reply_to(message, "🤖 Bot Version: v3.0 - REFACTORED MENU")

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        from bot.onboarding import start_onboarding
        start_onboarding(message, bot)

    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def handle_message(message):
        user_id = message.from_user.id
        user = db.get_user(user_id)
        
        if not user:
            from bot.onboarding import start_onboarding
            start_onboarding(message, bot)
            return

        lang = user.get('language', 'uz')
        text = message.text
        key = get_key_by_text(text)
        
        # --- Main Menu ---
        if key == "btn_calorie" or key == "btn_calorie_premium":
            handle_calorie_button(message, bot, onboarding.manager)
            
        elif key == "btn_habits":
            bot.send_message(user_id, get_text("choose_habit", lang) if "choose_habit" in TRANS[lang] else "Odatni tanlang:", reply_markup=habits_inline_keyboard(lang))
            
        elif key == "btn_trainer":
            bot.send_message(user_id, get_text("choose_plan_type", lang), reply_markup=plan_inline_keyboard(lang))
            
        elif key == "btn_challenges":
            bot.send_message(user_id, get_text("choose_challenge", lang) if "choose_challenge" in TRANS[lang] else "Chellenjni tanlang:", reply_markup=challenges_inline_keyboard(lang))
            
        elif key == "btn_premium":
            premium.handle_premium_menu(message, bot)
            
        elif key == "btn_profile":
            profile.handle_profile(message, bot)
            
        elif key == "btn_referral":
            gamification.handle_referral_link(message, bot)
            
        elif key == "btn_feedback":
            feedback.handle_feedback_start(message, bot)

        # --- Sub-Menus ---
        elif key == "back": # Back button
            # We need to know where to go back to. Usually Main Menu.
            bot.send_message(user_id, get_text("main_menu", lang) if "main_menu" in TRANS[lang] else "🏠 Asosiy menyu", reply_markup=main_menu_keyboard(lang))
            
        elif key == "btn_back_premium":
             premium.handle_premium_menu(message, bot)

        # Plan
        elif key == "btn_ai_workout":
            workout.generate_ai_workout(message, bot)
        elif key == "btn_ai_meal":
            workout.generate_ai_meal(message, bot)
            
        # Habits
        elif key == "btn_water": trackers.handle_water_tracker(message, bot)
        elif key == "btn_sleep": trackers.handle_sleep_tracker(message, bot)
        elif key == "btn_mood": trackers.handle_mood_tracker(message, bot)
        elif key == "btn_steps": trackers.handle_steps_tracker(message, bot)
        elif key == "btn_habit_stats": trackers.handle_habits_stats(message, bot)
        
        # AI Tools
        elif key == "btn_ai_qa": ai_features.handle_ai_qa(message, bot)
        elif key == "btn_ai_recipe": ai_features.handle_recipe_gen(message, bot)
        elif key == "btn_ai_shopping": ai_features.handle_shopping_list(message, bot)
        
        # Points
        elif key == "btn_points": gamification.handle_my_points(message, bot)
        elif key == "btn_rewards": gamification.handle_rewards(message, bot)
        elif key == "btn_rules": gamification.handle_rules(message, bot)
        
        # Challenges
        elif key == "btn_weekly_challenge": challenges.handle_weekly_challenge(message, bot)
        elif key == "btn_monthly_challenge": challenges.handle_monthly_challenge(message, bot)
        elif key == "btn_friends_challenge": challenges.handle_friends_challenge(message, bot)
        elif key == "btn_leaderboard": challenges.show_leaderboard_message(message, bot)
        
        # Profile
        elif key == "btn_edit_profile": profile.handle_edit_profile_command(message, bot)
        elif key == "btn_health_stats": profile.handle_profile_stats(message, bot)
        elif key == "btn_change_goal": profile.handle_change_goal_command(message, bot)
        
        # Premium
        elif key == "btn_buy_premium": premium.handle_premium_buy(message, bot)
        elif key == "btn_tariffs": premium.handle_premium_info(message, bot)
        
        else:
            # Check for states
            state = onboarding.manager.get_state(user_id)
            if state == trackers.STATE_STEPS_INPUT:
                trackers.process_steps_input(message, bot)
            elif state == trackers.STATE_SLEEP_INPUT:
                trackers.process_sleep_input(message, bot)
            elif state == trackers.STATE_MOOD_REASON:
                trackers.process_mood_reason(message, bot)
            elif state == calorie_scanner.STATE_CALORIE_TEXT:
                calorie_scanner.handle_calorie_text(message, bot)
            else:
                # Unknown command
                bot.reply_to(message, "⚠️ Tushunarsiz buyruq. Iltimos, menyudan foydalaning.")

    # Debug callback LAST
    @bot.callback_query_handler(func=lambda call: True)
    def debug_callback(call):
        print(f"DEBUG: Unhandled callback: {call.data}")
        bot.answer_callback_query(call.id, "⚠️ Bu tugma hali ishlamayapti")
        
    # Debug message handler
    @bot.message_handler(func=lambda m: True)
    def debug_message(message):
        print(f"DEBUG: Unhandled message: {message.text}")
        # Optional: bot.reply_to(message, "Tushunmadim. Menyudan tanlang.")

