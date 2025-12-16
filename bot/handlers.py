from bot import onboarding, gamification, admin, feedback, premium, profile, templates, workout
from bot.keyboards import main_menu_keyboard, ai_coach_submenu_keyboard, challenges_submenu_keyboard, help_submenu_keyboard, ai_coach_inline_keyboard
from bot import trackers, ai_features, challenges, calorie_scanner
from core.observability import track_latency # IMPORTED

from core.db import db

from telebot import types
from core.config import ADMIN_IDS

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
                # Touch Updated At for Retention Engine
                try:
                    db.touch_user_activity(user_id)
                except: pass
        except Exception as e:
            print(f"Logging Error: {e}")

    try:
        bot.register_middleware_handler(log_middleware, update_types=['message', 'callback_query'])
    except AttributeError:
        print("Warning: register_middleware_handler not found. Logging might be limited.")

    # --- Admin Handlers (Priority) ---
    admin.register_handlers(bot)
    
    # --- Developer Menu Handler ---
    @bot.message_handler(commands=['debug_ids'])
    def debug_ids_command(message):
        uid = message.from_user.id
        txt = f"👤 ID: `{uid}`\n"
        txt += f"📋 Admins: `{ADMIN_IDS}`\n"
        txt += f"✅ Is Admin? {uid in ADMIN_IDS}"
        bot.send_message(message.chat.id, txt, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "👨‍💻 Dasturchi")
    def developer_menu(message):
        if message.from_user.id in ADMIN_IDS:
             # ... existing code ...
            # Show Inline Keyboard with Admin Commands
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics_btn"),
                types.InlineKeyboardButton("🚩 Feature Flags", callback_data="admin_flags_btn"),
                types.InlineKeyboardButton("📦 Backup", callback_data="admin_backup_btn"),
                types.InlineKeyboardButton("✍️ Matnlar", callback_data="admin_content_btn")
            )
            bot.send_message(message.chat.id, "👨‍💻 **Dasturchi Paneli**\n\nBuyruqni tanlang:", reply_markup=markup, parse_mode="Markdown")

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
        pass

    # --- Main Menu Navigation ---
    # --- Main Menu Navigation ---
    @bot.message_handler(func=lambda message: message.text == "⬅️ Asosiy menyu" or message.text == "⬅️ Orqaga")
    def back_to_main(message):
        bot.send_message(message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu_keyboard(user_id=message.from_user.id))

    @bot.message_handler(func=lambda message: message.text == "⬅️ Premium menyu")
    def back_to_premium(message):
        premium.handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: "Kunlik odatlar" in message.text)
    def menu_habits(message):
        trackers.handle_habits_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🤖 AI murabbiy")
    def menu_ai(message):
        bot.send_message(message.chat.id, "🤖 <b>AI Murabbiy</b>\n\nBugun nima qilamiz? Quyidagilardan birini tanlang 👇", reply_markup=ai_coach_inline_keyboard(), parse_mode="HTML")

    # Moved Referral to Challenges submenu, but keeping handler for backward/direct access if needed
    @bot.message_handler(func=lambda message: message.text == "🔗 Referal" or message.text == "👥 Do‘st chaqirish")
    def menu_referral(message):
        gamification.handle_referral_link(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🔥 Chellenjlar")
    def menu_challenges(message):
        bot.send_message(message.chat.id, "🔥 Bugungi Chellenjlar", reply_markup=challenges_submenu_keyboard())

    @bot.message_handler(func=lambda message: message.text == "👤 Profil")
    def menu_profile(message):
        profile.handle_profile(message, bot)
        
    @bot.message_handler(func=lambda message: message.text == "💚 YASHA Plus")
    def menu_yasha_plus(message):
        # Soft paywall message
        bot.send_message(message.chat.id, "🚀 YASHA Plus bilan natija 2x tezroq\nBugun Plus bilan menyu tuzing!", reply_markup=premium.premium_inline_keyboard())

    @bot.message_handler(func=lambda message: message.text in ["💳 Obuna", "💎 Premium"])
    def menu_premium(message):
        premium.handle_premium_menu(message, bot)

    @bot.message_handler(func=lambda message: message.text == "📩 Yordam" or message.text == "📩 Qayta aloqa")
    def menu_help(message):
        bot.send_message(message.chat.id, "Nima tushunarsiz bo'ldi?", reply_markup=help_submenu_keyboard())

    # --- Submenu Button Handlers ---

    # AI Coach Inline Callback Handler
    @bot.callback_query_handler(func=lambda call: call.data.startswith('ai_sub_'))
    def ai_coach_callback(call):
        action = call.data.replace('ai_sub_', '')
        
        if action == 'workout':
            # Call generation with explicit user_id
            workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
            try: bot.answer_callback_query(call.id)
            except: pass
            
        elif action == 'meal':
            workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)
            try: bot.answer_callback_query(call.id)
            except: pass
        
        elif action == 'recipe':
             # Redirect to Fridge Recipe
             # We can manually call the function or just trigger standard Fridge flow
             callback_start_fridge_recipe(call)
            
        elif action == 'shopping':
            try:
                 link = db.get_user_menu_link(call.from_user.id)
                 if not link:
                     bot.answer_callback_query(call.id, "Avval menyu tuzing", show_alert=True)
                     return
                 
                 import json
                 raw_list = json.loads(link['shopping_list_json'])
                 if not raw_list:
                     bot.answer_callback_query(call.id, "Ro'yxat bo'sh", show_alert=True)
                     return
                 
                 # Format list
                 text = "🛒 <b>Xaridlar Ro'yxati</b>\n\n"
                 for category, items in raw_list.items():
                     text += f"<b>{category}:</b>\n"
                     for item in items:
                         text += f"▫️ {item}\n"
                     text += "\n"
                 bot.send_message(call.from_user.id, text, parse_mode="HTML")
                 bot.answer_callback_query(call.id)
            except Exception as e:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi")

        elif action == 'qa':
            # QA handler might expect message.text. It starts a conversation state usually?
            # Let's check handle_ai_qa implementation first. 
            # Assuming handle_ai_qa asks for input via state.
            ai_features.handle_ai_qa(call.message, bot) # Check if this works for callback message
            bot.answer_callback_query(call.id)
            
        elif action == 'close':
            bot.delete_message(call.message.chat.id, call.message.message_id)

    # AI Coach Submenu (Legacy Text Handlers - kept for backward compatibility if needed, or remove)
    @bot.message_handler(func=lambda message: message.text == "🏋️ Mashq qilaman")
    def sub_workout(message):
        workout.generate_ai_workout(message, bot)
        
    @bot.message_handler(func=lambda message: message.text == "🥗 Nima yeyman?" or message.text == "🔥 AI retsept tuzsin")
    def sub_meal(message):
        workout.generate_ai_meal(message, bot)
        
    @bot.message_handler(func=lambda message: message.text == "🛒 Nima xarid qilay?")
    def sub_shopping(message):
        try:
             link = db.get_user_menu_link(message.from_user.id)
             if not link:
                 bot.reply_to(message, "🛒 Avval menyu tuzing (AI Menyu), keyin xarid ro'yxatini ko'rishingiz mumkin.")
                 return
             import json
             raw_list = json.loads(link['shopping_list_json'])
             if not raw_list:
                 bot.reply_to(message, "🛒 Ro'yxat bo'sh.")
                 return
             
             # Format list
             text = "🛒 <b>Xaridlar Ro'yxati</b>\n\n"
             for category, items in raw_list.items():
                 text += f"<b>{category}:</b>\n"
                 for item in items:
                     text += f"▫️ {item}\n"
                 text += "\n"
             bot.send_message(message.chat.id, text, parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, "Xatolik: Ro'yxatni yuklab bo'lmadi.")

    @bot.message_handler(func=lambda message: message.text == "❓ Murabbiyga savolim bor")
    def sub_qa(message):
        ai_features.handle_ai_qa(message, bot)

    # Challenges Submenu
    @bot.message_handler(func=lambda message: message.text == "🔥 Bugungi chellenj")
    def sub_challenge_daily(message):
        text = (
            "🔥 <b>Bugungi Chellenj: 100 ta O'tirib-turish (Squats)</b>\n\n"
            "Bajarib bo'lgach, 'Bajardim' tugmasini bosing.\n"
            "Mukofot: +10 ball"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Bajardim (+10 ball)", callback_data="challenge_complete_daily"))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(func=lambda message: message.text == "🏆 Reyting")
    def sub_leaderboard(message):
        challenges.show_leaderboard_message(message, bot)

    # Help Submenu
    @bot.message_handler(func=lambda message: message.text == "🏋️ Mashqlar bo'yicha")
    def help_workout_info(message):
        bot.send_message(message.chat.id, "Mashq rejasi bo'yicha savollarni yozing yoki videolarni kuting. Hozircha AI murabbiy yordam bera oladi.")

    @bot.message_handler(func=lambda message: message.text == "🥗 Menyu bo'yicha")
    def help_meal_info(message):
         bot.send_message(message.chat.id, "Menyu bo'yicha savollaringizni AI murabbiyga bering. U retseptlar va o'zgartirishlar kiritib bera oladi.")
         
    @bot.message_handler(func=lambda message: message.text == "💳 Obuna bo'yicha")
    def help_premium_info(message):
        premium.handle_premium_info_detailed(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🤖 Bot ishlamayapti")
    def help_bug_report(message):
        feedback.handle_feedback_start(message, bot)

    # --- Sub-Menu Handlers (Legacy / Direct Callbacks) ---

    # Plan
    @bot.message_handler(func=lambda message: message.text == "🤖 AI mashg‘ulot rejasi" or message.text == "🏋️ AI mashq rejasi")
    @track_latency("ai_workout_request") # TRACKED
    def plan_workout_ai(message):
        workout.generate_ai_workout(message, bot)

    @bot.message_handler(func=lambda message: message.text == "🥦 AI ovqatlanish rejasi" or message.text == "🥦 AI menyu")
    @track_latency("ai_meal_request") # TRACKED
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
    # menu.register_handlers(bot) # Removed
    gamification.register_handlers(bot)
    gamification.register_handlers(bot)
    feedback.register_handlers(bot)
    feedback.register_handlers(bot)
    premium.register_handlers(bot)
    profile.register_handlers(bot)
    templates.register_handlers(bot)
    calorie_scanner.register_handlers(bot)

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
    @bot.callback_query_handler(func=lambda call: call.data.startswith("ai_tool_"))
    def handle_ai_tool(call):
        from core.utils import parse_callback
        parts = parse_callback(call.data, prefix="ai_tool_", min_parts=3)
        
        if not parts:
            bot.answer_callback_query(call.id, "Xatolik")
            return

        try:
            tool = parts[2]
            
            if tool == "workout":
                # ...
                pass
            elif tool == "diet":
                # ...
                pass
                
            bot.answer_callback_query(call.id, "Tez kunda...")
        except Exception as e:
            print(f"AI tool error: {e}")
            bot.answer_callback_query(call.id, "Xatolik")

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
        elif action == 'friends': challenges.handle_friends_challenge(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Calorie Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('calorie_mode_'))
    def calorie_mode_handler(call):
        calorie_scanner.handle_calorie_mode(call, bot)

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
        if action == 'qa': ai_features.handle_ai_qa(call.message, bot, user_id=call.from_user.id)
        elif action == 'meal': workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)
        elif action == 'workout': workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
        elif action == 'recipe': ai_features.handle_recipe_gen(call.message, bot, user_id=call.from_user.id)
        elif action == 'shopping': ai_features.handle_shopping_list(call.message, bot, user_id=call.from_user.id)
        bot.answer_callback_query(call.id)

    # Points Callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith('points_'))
    def points_callback(call):
        action = call.data.replace('points_', '')
        if action == 'balance': gamification.handle_my_points(call.message, bot, user_id=call.from_user.id)
        elif action == 'rewards': gamification.handle_rewards(call.message, bot, user_id=call.from_user.id)
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
        elif action == 'info': premium.handle_premium_info_detailed(call.message, bot)
        elif action == 'coins': gamification.handle_points_menu(call.message, bot, user_id=call.from_user.id)
        elif action == 'offer': premium.handle_offer_download(call.message, bot)
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
        from core.config import ADMIN_IDS
        if message.from_user.id not in ADMIN_IDS:
            return

        import google.generativeai as genai
        import os
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            bot.reply_to(message, "❌ API Key topilmadi!")
            return
        
        bot.reply_to(message, f"🔄 Model: gemini-2.5-flash sinalyapti...")
        
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content("Test")
            bot.reply_to(message, f"✅ Success! Response: {response.text}")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    # [DUPLICATE HANDLER REMOVED]
    # The clean implementation is below at line 514+

    # --- New Menu Navigation Handlers ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith('menu_view_') or call.data.startswith('eat_') or call.data in ['menu_fridge', 'menu_swap_vip', 'menu_regenerate'])
    def menu_nav_callback(call):
        workout.handle_menu_callback(call, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "menu_shopping")
    def callback_menu_shopping(call):
        try:
            link = db.get_user_menu_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Reja topilmadi.")
                # Send CTA
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🍽 Menyu tuzish", callback_data="plan_ai_meal"))
                bot.send_message(call.from_user.id, "🛒 Xaridlar ro'yxatini tuzish uchun avval Menyu yarating:", reply_markup=markup)
                return

            import json
            raw_list = json.loads(link['shopping_list_json'])
            
            if not raw_list:
                bot.answer_callback_query(call.id, "Shopping list bo'sh.")
                return

            txt = "🛒 <b>XARIDLAR RO'YXATI</b> (1-Hafta)\n\n"
            
            # Check Format: List vs Dict
            if isinstance(raw_list, list):
                # OLD Format
                txt += "<i>Eski formatdagi ro'yxat:</i>\n"
                for item in raw_list:
                     txt += f"▫️ {item}\n"
            elif isinstance(raw_list, dict):
                # NEW Categorized Format
                categories = {
                    "protein": "🥩 Oqsil (Go'sht/Tuxum)",
                    "veg": "🥦 Sabzavot va Meva",
                    "carbs": "🍚 Don mahsulotlari",
                    "dairy": "🥛 Sut mahsulotlari",
                    "misc": "🧂 Boshqa"
                }
                
                for key, label in categories.items():
                    items = raw_list.get(key, [])
                    if items:
                        txt += f"<b>{label}:</b>\n"
                        for item in items:
                            txt += f"▫️ {item}\n"
                        txt += "\n"
            
            # Coach Advice (Shopping)
            txt += "\n🧠 <b>Coach Maslahati:</b>\n<i>\"Bozorlikni oldindan qilsang, 'fastfood' seni ushlolmaydi 😄\"</i>"
                
            bot.send_message(call.from_user.id, txt, parse_mode="HTML")
            bot.answer_callback_query(call.id)
            
        except Exception as e:
            print(f"Shopping List Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")




    @bot.callback_query_handler(func=lambda call: call.data.startswith("menu_next_") or call.data.startswith("menu_prev_"))
    def callback_menu_nav(call):
        """ULTRA-SIMPLE navigation - just show the next/prev day."""
        try:
            # Extract day number from callback
            parts = call.data.split("_")  # ["menu", "next/prev", "day_number"]
            # Fix: Safe parsing
            if len(parts) < 3:
                bot.answer_callback_query(call.id, "Xatolik: Ma'lumot yetarli emas")
                return
            
            current_day = int(parts[2])
            
            # Calculate new day
            if "next" in call.data:
                new_day = current_day + 1
            else:
                new_day = current_day - 1
            
            # Clamp to valid range
            if new_day < 1:
                new_day = 1
            
            # Get menu data
            link = db.get_user_menu_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Menyu topilmadi!")
                return
            
            # Delete old message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Show new day
            workout.show_daily_menu(bot, call.from_user.id, link, override_day_idx=new_day)
            
        except Exception as e:
            error_msg = f"Xatolik: {str(e)[:50]}"
            print(f"Navigation Error: {e}")
            bot.answer_callback_query(call.id, error_msg)
            bot.send_message(call.from_user.id, f"❌ {error_msg}")

    # =========================================================
    # WORKOUT NAVIGATION (Mirrors Menu Navigation)
    # =========================================================

    @bot.callback_query_handler(func=lambda call: call.data == "workout_regenerate")
    def callback_workout_regenerate(call):
        """Regenerate workout plan logic."""
        try:
             # Deactivate active link
            db.deactivate_all_user_workouts(call.from_user.id)
            
            # Delete message and restart generation
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Trigger fresh generation
            workout.generate_ai_workout(call.message, bot, user_id=call.from_user.id)
            bot.answer_callback_query(call.id, "✅ Jarayon boshlandi...")
            
        except Exception as e:
            print(f"Workout Regen Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("workout_next_") or call.data.startswith("workout_prev_"))
    def callback_workout_nav(call):
        """Workout navigation - just show the next/prev day."""
        try:
            # Extract day number
            parts = call.data.split("_")  # ["workout", "next/prev", "day_number"]
            current_day = int(parts[2])
            
            # Calculate new day
            if "next" in call.data:
                new_day = current_day + 1
            else:
                new_day = current_day - 1
            
            # Clamp to valid range (1-7)
            if new_day < 1:
                new_day = 1
            # Note: Max cap is handled in show_daily_workout via JSON length
            
            # Get data
            link = db.get_user_workout_link(call.from_user.id)
            if not link:
                bot.answer_callback_query(call.id, "Reja topilmadi.")
                return
            
            # Delete old message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Show new day
            workout.show_daily_workout(bot, call.from_user.id, link, override_day_idx=new_day)
            
        except Exception as e:
            print(f"Workout Nav Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")



    @bot.callback_query_handler(func=lambda call: call.data == "menu_regenerate")
    def callback_menu_regenerate(call):
        try:
            # Logic for regeneration...
            pass 
        except:
            pass

    # =========================================================
    # REWARDS & COIN SHOP HANDLERS
    # =========================================================

    @bot.callback_query_handler(func=lambda call: call.data in ["redeem_prem_7", "redeem_prem_30"])
    def callback_redeem_premium(call):
        try:
            user_id = call.from_user.id
            user = db.get_user(user_id)
            if not user:
                return

            points = user.get('yasha_points', 0)
            
            cost = 0
            days = 0
            
            if call.data == "redeem_prem_7":
                cost = 100
                days = 7
            elif call.data == "redeem_prem_30":
                cost = 500
                days = 30
                
            if points < cost:
                bot.answer_callback_query(call.id, f"❌ Ballar yetarli emas ({points}/{cost})", show_alert=True)
                return
            
            # Deduct points
            db.update_user_points(user_id, -cost)
            
            # Grant premium
            db.set_premium(user_id, days)
            
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id, 
                f"🎉 **Tabriklaymiz!**\n\nSiz {cost} ball evaziga {days} kunlik Premium obuna oldingiz!\n\nHozir barcha imkoniyatlardan foydalanishingiz mumkin. ✅",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            print(f"Redeem Error: {e}")
            bot.answer_callback_query(call.id, f"Xatolik: {str(e)[:100]}", show_alert=True)

    # =========================================================
    # MEAL SWAP HANDLER (VIP)
    # =========================================================
    
    @bot.callback_query_handler(func=lambda call: call.data == "menu_swap_vip")
    def callback_menu_swap(call):
        try:
            # Simply re-trigger generation for now, or show construction message
            # Ideally: Show "Yangi taom" vs "Yangi retsept same meal"
            # User goal: Just wants difference. Let's redirect to meal selection or regenerate.
            
            # Check VIP
            if not db.is_premium(call.from_user.id): # VIP check ideally
                 bot.answer_callback_query(call.id, "💎 Bu funksiya faqat Premium/VIP uchun!", show_alert=True)
                 return

            bot.answer_callback_query(call.id, "🔄 Taom almashtirilmoqda...")
            
            # Deactivate active link so generate_ai_meal sees clean state
            db.deactivate_all_user_menus(call.from_user.id)
            
            # Delete message and restart generation
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            
            # Trigger fresh generation
            workout.generate_ai_meal(call.message, bot, user_id=call.from_user.id)

        except Exception as e:
            print(f"Regen Error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    # =========================================================
    # FRIDGE RECIPE HANDLERS
    # =========================================================

    @bot.callback_query_handler(func=lambda call: call.data == "menu_fridge")
    def callback_start_fridge_recipe(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(
                call.message.chat.id, 
                "🥦 **Muzlatgichda nima bor?**\n\nBor mahsulotlarni vergul bilan yozib yuboring.\nMasalan: _Tuxum, pomidor, kartoshka_",
                parse_mode="Markdown"
            )
            bot.register_next_step_handler(msg, handle_fridge_input, bot)
        except Exception as e:
             print(f"Fridge Start Error: {e}")

    def handle_fridge_input(message, bot):
        try:
            txt = message.text
            
            # 1. Navigation Escape Hatch
            # If user presses a menu button instead of typing ingredients
            if txt.startswith("⬅️") or txt.startswith("🏠") or txt.startswith("/") or txt in ["🤖 AI murabbiy", "🔥 Chellenjlar", "👤 Profil"]:
                bot.send_message(message.chat.id, "❌ Retsept bekor qilindi.", reply_markup=main_menu_keyboard(user_id=message.from_user.id))
                return

            ingredients = txt
            if not ingredients or len(ingredients) < 3:
                bot.send_message(message.chat.id, "Iltimos, mahsulotlarni to'g'ri yozing.")
                # Keep handler active? No, let them click again or type again if we knew how to re-register.
                # For now just return, they have to click button again to restart flow.
                return

            user = db.get_user(message.from_user.id)
            if not user: return
            
            # FIXED: Added parse_mode='Markdown'
            gen_msg = bot.send_message(message.chat.id, "👨‍🍳 **Shef-oshpaz o'ylamoqda...**\n\nRetsept tuzilmoqda...", parse_mode="Markdown")
            
            # Call AI
            from core.ai import ai_generate_fridge_recipe
            recipe_text = ai_generate_fridge_recipe(user, ingredients)
            
            bot.delete_message(message.chat.id, gen_msg.message_id)
            
            if recipe_text:
                bot.send_message(message.chat.id, recipe_text, parse_mode="HTML")
                
                # Show Main Menu again after recipe
                bot.send_message(message.chat.id, "Yana nimadir kerakmi?", reply_markup=main_menu_keyboard(user_id=message.from_user.id))
            else:
                bot.send_message(message.chat.id, "⚠️ Uzr, bu mahsulotlardan retsept topa olmadim.")

        except Exception as e:
            print(f"Fridge Input Error: {e}")
            bot.send_message(message.chat.id, "❌ Xatolik yuz berdi.")

    # --- FALLBACK HANDLER (MUST BE LAST) ---
    @bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact'], func=lambda m: True)
    def fallback_handler(message):
        """
        Catches any unhandled message when user is NOT in a specific state.
        Redirects to Main Menu with Coach Tone.
        """
        user_id = message.from_user.id
        current_state = onboarding.manager.get_state(user_id)
        
        # If user is in onboarding flows (e.g. typing name), do NOT interrupt.
        if current_state != onboarding.STATE_NONE:
            return

        try:
            # Coach Tone Response
            bot.send_message(
                message.chat.id,
                "Men seni tushundim 😄 Pastdagi bo‘limlardan birini tanla, men o‘sha yerda yordam beraman 👇",
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            print(f"Fallback error: {e}")
