from telebot import types
from core.db import db
from bot.keyboards import gender_keyboard, goal_keyboard, allergy_keyboard

def handle_profile(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        return

    is_premium = db.is_premium(user_id)
    prem_status = "Ha ✅" if is_premium else "Yo‘q ❌"
    
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"👤 Ism: {user['name']}\n"
        f"🎂 Yosh: {user['age']}\n"
        f"🚻 Jins: {user['gender']}\n"
        f"📏 Bo‘y: {user['height']} sm\n"
        f"⚖️ Vazn: {user['weight']} kg\n"
        f"🎯 Maqsad: {user['goal']}\n"
        f"🤧 Allergiya: {user['allergy']}\n"
        f"💎 Premium: {prem_status}\n"
        f"💰 Ballar: {user['points']}\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎂 Yoshni o‘zgartirish", callback_data="edit_age"))
    markup.add(types.InlineKeyboardButton("🚻 Jinsni o‘zgartirish", callback_data="edit_gender"))
    markup.add(types.InlineKeyboardButton("📏 Bo‘y/Vaznni o‘zgartirish", callback_data="edit_body"))
    markup.add(types.InlineKeyboardButton("🎯 Maqsadni o‘zgartirish", callback_data="edit_goal"))
    markup.add(types.InlineKeyboardButton("🤧 Allergiyani o‘zgartirish", callback_data="edit_allergy"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
    def handle_edit_callback(call):
        action = call.data.split("_")[1]
        user_id = call.from_user.id
        
        if action == "age":
            msg = bot.send_message(user_id, "Yangi yoshingizni kiriting (raqamda):")
            bot.register_next_step_handler(msg, save_age, bot)
        elif action == "gender":
            bot.send_message(user_id, "Yangi jinsni tanlang:", reply_markup=gender_keyboard())
        elif action == "body":
            msg = bot.send_message(user_id, "Yangi bo‘yingizni kiriting (sm):")
            bot.register_next_step_handler(msg, save_height, bot)
        elif action == "goal":
            bot.send_message(user_id, "Yangi maqsadni tanlang:", reply_markup=goal_keyboard())
        elif action == "allergy":
            bot.send_message(user_id, "Sizda allergiya bormi?", reply_markup=allergy_keyboard())
            
        bot.answer_callback_query(call.id)

    # --- Save Handlers ---
    def save_age(message, bot):
        if not message.text.isdigit():
            msg = bot.send_message(message.chat.id, "Iltimos, raqam kiriting:")
            bot.register_next_step_handler(msg, save_age, bot)
            return
        db.update_user_profile(message.from_user.id, age=int(message.text))
        bot.send_message(message.chat.id, "✅ Yosh yangilandi!")
        handle_profile(message, bot)

    def save_height(message, bot):
        if not message.text.isdigit():
            msg = bot.send_message(message.chat.id, "Iltimos, raqam kiriting (sm):")
            bot.register_next_step_handler(msg, save_height, bot)
            return
        db.update_user_profile(message.from_user.id, height=int(message.text))
        msg = bot.send_message(message.chat.id, "Endi yangi vazningizni kiriting (kg):")
        bot.register_next_step_handler(msg, save_weight, bot)

    def save_weight(message, bot):
        try:
            weight = float(message.text.replace(',', '.'))
            db.update_user_profile(message.from_user.id, weight=weight)
            bot.send_message(message.chat.id, "✅ Bo‘y va vazn yangilandi!")
            handle_profile(message, bot)
        except ValueError:
            msg = bot.send_message(message.chat.id, "Iltimos, to‘g‘ri raqam kiriting:")
            bot.register_next_step_handler(msg, save_weight, bot)

    # Re-use existing callback handlers logic for gender/goal/allergy but specifically for editing
    # Since we already have global handlers in onboarding.py for 'gender_', 'goal_', 'allergy_', 
    # we need to be careful not to conflict or duplicate.
    # The onboarding handlers use `process_gender` etc. which update `onboarding_data`.
    # We need handlers that update DB directly.
    # Let's use different callback prefixes for editing to avoid conflict: 'update_gender_', 'update_goal_', 'update_allergy_'
    # BUT wait, the keyboards return 'gender_male' etc.
    # If we reuse the keyboards, we get the same callbacks.
    # We should probably update `onboarding.py` handlers to check if it's onboarding or editing?
    # OR simpler: just handle the update here and let `onboarding.py` handle its own state.
    # But `onboarding.py` handlers catch `call.data.startswith('gender_')`.
    # So if I click 'gender_male' here, `onboarding.py` will catch it.
    # `onboarding.py` uses `onboarding_data`. If user is not in `onboarding_data`, it might crash or do nothing.
    
    # FIX: I will modify `bot/keyboards.py` to accept a prefix? No, too many changes.
    # Better: I will modify `bot/onboarding.py` to ONLY handle if user is in `onboarding_data`.
    # And here I will handle if user is NOT in `onboarding_data`.
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
    def update_gender(call):
        # Check if this is for profile update (not onboarding)
        # We can check if user is in onboarding_data (we need to import it or check DB state)
        # Simplest: Just update DB. If it's onboarding, it will be overwritten later? No.
        # Let's check if user exists in DB and is fully registered.
        # Actually, `onboarding.py` handlers are registered FIRST in `handlers.py`?
        # If so, they might intercept.
        # Let's assume we can share the handler or make it smart.
        
        # For this refactor, I'll implement specific update handlers that check if user is registered.
        user_id = call.from_user.id
        # If user is editing profile, they are already in DB.
        # We can just update DB.
        gender = "Erkak" if call.data == "gender_male" else "Ayol"
        db.update_user_profile(user_id, gender=gender)
        bot.answer_callback_query(call.id, "Jins yangilandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('goal_'))
    def update_goal(call):
        user_id = call.from_user.id
        goals = {
            "goal_weight_loss": "Ozish",
            "goal_muscle_gain": "Massa olish",
            "goal_health": "Sog‘liqni tiklash"
        }
        goal = goals.get(call.data, "Sog‘liq")
        db.update_user_profile(user_id, goal=goal)
        bot.answer_callback_query(call.id, "Maqsad yangilandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('allergy_'))
    def update_allergy(call):
        user_id = call.from_user.id
        if call.data == "allergy_yes":
            msg = bot.send_message(user_id, "Nimalarga allergiyangiz bor? Yozib qoldiring:")
            bot.register_next_step_handler(msg, save_allergy_text, bot)
        else:
            db.update_user_profile(user_id, allergy="Yo‘q")
            bot.answer_callback_query(call.id, "Allergiya yangilandi!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            handle_profile(call.message, bot)

    def save_allergy_text(message, bot):
        db.update_user_profile(message.from_user.id, allergy=message.text)
        bot.send_message(message.chat.id, "✅ Allergiya ma'lumotlari yangilandi!")
        handle_profile(message, bot)
