from bot import onboarding, menu, gamification, admin, feedback, premium, profile, templates, workout
from bot.calories import handle_calorie_button, handle_food_photo, STATE_CALORIE_PHOTO
from bot.keyboards import main_menu_keyboard
from bot import trackers, ai_features, challenges, calorie_scanner

def register_all_handlers(bot):
    # --- Calorie Handlers ---
    @bot.message_handler(func=lambda message: message.text == "🍽 Kaloriya tahlili (premium)" or message.text == "🍽 Kaloriya skaneri")
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

    @bot.message_handler(func=lambda message: message.text == "🏋️ Mening Rejam")
    def menu_plan(message):
        workout.handle_plan_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔁 Odatlar")
    def menu_habits(message):
        trackers.handle_habits_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🎯 Shaxsiy Murabbiy")
    def menu_ai(message):
        ai_features.handle_ai_tools_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🟡 Yasha Ball")
    def menu_points(message):
        gamification.handle_points_menu(message, bot)

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
        bot.send_message(message.chat.id, "🚶 **Qadamlar**\n\nTez kunda avtomatik hisoblash qo'shiladi!", parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "📊 Odatlar statistikasi")
    def habit_stats(message):
        trackers.handle_habits_stats(message, bot)

    # AI Tools
    @bot.message_handler(func=lambda message: message.text == "❓ AI savol-javob")
    def ai_qa(message):
        ai_features.handle_ai_qa(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🍳 AI retsept")
    def ai_recipe(message):
        ai_features.handle_recipe_gen(message, bot)

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
        elif type == 'sleep': trackers.process_sleep_callback(call, bot)
        elif type == 'mood': trackers.process_mood_callback(call, bot)

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
        action = call.data.split('_')[1]
        if action == 'daily': challenges.handle_daily_challenge(call, bot)
        elif action == 'leaderboard': challenges.show_leaderboard(call, bot)
        elif action == 'complete': 
            challenges.complete_challenge(call, bot, 10)
        bot.answer_callback_query(call.id)

    # Calorie Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('calorie_mode_'))
    def calorie_mode_handler(call):
        calorie_scanner.calorie_mode_callback(call, bot)

    @bot.message_handler(func=lambda message: onboarding.manager.get_state(message.from_user.id) == calorie_scanner.STATE_CALORIE_TEXT)
    def text_calorie_handler(message):
        calorie_scanner.handle_calorie_text(message, bot)

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

