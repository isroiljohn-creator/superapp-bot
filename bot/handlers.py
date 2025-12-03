from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates, workout
from bot.calories import handle_calorie_button, handle_food_photo, STATE_CALORIE_PHOTO
from bot.keyboards import main_menu_keyboard
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
    # --- Calorie Handlers ---
    @bot.message_handler(func=lambda message: message.text == "🍽 Kaloriya tahlili (premium)" or message.text == "🍽 Kaloriya skaneri" or message.text == "🍽 Kaloriya tahlili")
    def calorie_handler(message):
        calorie_scanner.show_calorie_menu(message, bot)

    @bot.message_handler(content_types=['photo'])
    def photo_handler(message):
        # Check for calorie scanner state
        state = onboarding.manager.get_state(message.from_user.id)
        if state == calorie_scanner.STATE_CALORIE_PHOTO:
            calorie_scanner.handle_calorie_photo(message, bot)
            return
        
        # Check for feedback state (if implemented via state, but feedback uses next_step_handler usually)
        # If no state, ignore or handle as generic photo
        pass

    # --- Main Menu Navigation ---
    @bot.message_handler(func=lambda message: message.text == "⬅️ Asosiy menyu")
    def back_to_main(message):
        bot.send_message(message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu_keyboard())

    @bot.message_handler(func=lambda message: message.text == "⬅️ Premium menyu")
    def back_to_premium(message):
        premium.handle_premium_menu(message, bot)

    # @bot.message_handler(func=lambda message: message.text == "🏋️ Mening Rejam")
    # def menu_plan(message):
    #     workout.handle_plan_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔁 Odatlar")
    def menu_habits(message):
        trackers.handle_habits_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🎯 Shaxsiy Murabbiy")
    def menu_ai(message):
        ai_features.handle_ai_tools_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔗 Referal")
    def menu_referral(message):
        gamification.handle_referral_link(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔥 Chellenjlar")
    def menu_challenges(message):
        challenges.handle_challenges_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "👤 Profil")
    def menu_profile(message):
        profile.handle_profile(message, bot)

    @bot.message_handler(func=lambda message: message.text == "💎 Premium")
    def menu_premium(message):
        premium.handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📩 Qayta aloqa")
    def menu_feedback(message):
        feedback.handle_feedback_start(message, bot)

    # --- Sub-Menu Handlers ---

    # Plan
    @bot.message_handler(func=lambda message: message.text == "🤖 AI mashg‘ulot rejasi" or message.text == "🏋️ AI mashq rejasi")
    def plan_workout_ai(message):
        workout.generate_ai_workout(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🥦 AI ovqatlanish rejasi" or message.text == "🥦 AI menyu")
    def plan_meal_ai(message):
        workout.generate_ai_meal(message, bot)

    # Habits
    @bot.message_handler(func=lambda message: message.text == "💧 Suv ichish")
    def habit_water(message):
        trackers.handle_water_tracker(message, bot)

    @bot.message_handler(func=lambda message: message.text == "😴 Uyqu")
    def habit_sleep(message):
        trackers.handle_sleep_tracker(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🙂 Kayfiyat")
    def habit_mood(message):
        trackers.handle_mood_tracker(message, bot)
        
    @bot.message_handler(func=lambda message: message.text == "🚶 Qadamlar")
    def habit_steps(message):
        trackers.handle_steps_tracker(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📊 Odatlar statistikasi")
    def habit_stats(message):
        trackers.handle_habits_stats(message, bot)

    # Habits Input Handlers
    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == trackers.STATE_STEPS_INPUT)
    def steps_input_handler(message):
        trackers.process_steps_input(message, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == trackers.STATE_SLEEP_INPUT)
    def sleep_input_handler(message):
        trackers.process_sleep_input(message, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == trackers.STATE_MOOD_REASON)
    def mood_reason_handler(message):
        trackers.process_mood_reason(message, bot)
        
    # AI Tools


    @bot.message_handler(func=lambda message: message.text == "🛒 AI shopping list")
    def ai_shopping(message):
        ai_features.handle_shopping_list(message, bot)

    # Points
    @bot.message_handler(func=lambda message: message.text == "📊 Ballarim")
    def points_my(message):
        gamification.handle_my_points(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🎁 Mukofotlar")
    def points_rewards(message):
        gamification.handle_rewards(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📜 Qoidalar")
    def points_rules(message):
        gamification.handle_rules(message, bot)

    # Challenges
    @bot.message_handler(func=lambda message: message.text == "📆 Haftalik challenge")
    def challenge_weekly(message):
        challenges.handle_weekly_challenge(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🗓 Oylik challenge")
    def challenge_monthly(message):
        challenges.handle_monthly_challenge(message, bot)

    @bot.message_handler(func=lambda message: message.text == "👥 Do‘stlar challenge")
    def challenge_friends(message):
        challenges.handle_friends_challenge(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🏆 Leaderboard")
    def challenge_leaderboard(message):
        challenges.show_leaderboard_message(message, bot)

    # Profile
    @bot.message_handler(func=lambda message: message.text == "✏️ Ma’lumotlarni tahrirlash")
    def profile_edit(message):
        profile.handle_edit_profile_command(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📊 Sog‘liq statistikasi")
    def profile_stats(message):
        profile.handle_profile_stats(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🎯 Maqsadni o‘zgartirish")
    def profile_goal(message):
        profile.handle_change_goal_command(message, bot)

    # Premium
    @bot.message_handler(func=lambda message: message.text == "💳 Premium sotib olish")
    def premium_buy(message):
        premium.handle_premium_buy(message, bot)

    @bot.message_handler(func=lambda message: message.text == "ℹ️ Tariflar")
    def premium_info(message):
        premium.handle_premium_info(message, bot)

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
        bot.answer_callback_query(call.id)

    # AI Tool Callbacks (if any left using callbacks)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('ai_tool_'))
    def ai_tool_callback(call):
        tool = call.data.split('_')[2]
        if tool == 'shopping': ai_features.handle_shopping_list(call.message, bot)
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
        bot.reply_to(message, "🤖 Bot Version: v3.1 - FIXES APPLIED (Dec 3)")

    @bot.message_handler(commands=['debug_ai'])
    def handle_debug_ai(message):
        import google.generativeai as genai
        import os
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            bot.reply_to(message, "❌ API Key topilmadi!")
            return
        
        bot.reply_to(message, f"🔑 Key: {key[:5]}...{key[-5:]}\n🔄 Model: gemini-2.5-flash sinalyapti...")
        
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content("Test")
            bot.reply_to(message, f"✅ Success! Response: {response.text}")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

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

