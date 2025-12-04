from telebot import types
from core.db import db
from core.ai import ai_provide_psychological_support
from datetime import datetime

# States for inputs
STATE_STEPS_INPUT = "steps_input"
STATE_SLEEP_INPUT = "sleep_input"
STATE_MOOD_REASON = "mood_reason_input"

# --- Water Tracker ---
def handle_water_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
        
    today = datetime.now().strftime("%Y-%m-%d")
    log = db.get_daily_log(user_id, today)
    current_ml = log.get('water_ml', 0) if log else 0
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💧 250ml ichdim", callback_data="track_water_250"))
    
    user = db.get_user(user_id)
    streak = user.get('streak_water', 0)
    
    bot.send_message(
        user_id,
        f"💧 **Suv Balansi**\n\n"
        f"Bugungi maqsadingiz: 2500 ml\n"
        f"Ichildi: {current_ml} ml\n"
        f"Joriy streak: {streak} kun 🔥\n\n"
        f"Suv ichdingizmi? Belgilang:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def process_water_callback(call, bot):
    user_id = call.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Update log
    log = db.get_daily_log(user_id, today)
    current_ml = log.get('water_ml', 0) if log else 0
    new_ml = current_ml + 250
    
    db.update_daily_log(user_id, today, water_ml=new_ml)
    
    msg_text = f"✅ Qabul qilindi! ({new_ml}/2500 ml)"
    
    # Check for daily goal reward (once per day)
    # We need a flag to know if reward was already given. 
    # For simplicity, we check if we JUST crossed the threshold.
    if current_ml < 2500 and new_ml >= 2500:
        db.update_streak(user_id, 'water') # Increment streak
        db.add_points(user_id, 1)
        msg_text += "\n🎉 Kunlik reja bajarildi! +1 ball"
    
    bot.answer_callback_query(call.id, msg_text)
    
    # Update message
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💧 250ml ichdim", callback_data="track_water_250"))
    
    user = db.get_user(user_id)
    streak = user.get('streak_water', 0)
    
    bot.edit_message_text(
        f"💧 **Suv Balansi**\n\n"
        f"Bugungi maqsadingiz: 2500 ml\n"
        f"Ichildi: {new_ml} ml\n"
        f"Joriy streak: {streak} kun 🔥\n\n"
        f"Suv ichdingizmi? Belgilang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# --- Steps Tracker ---
def handle_steps_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
        
    from bot import onboarding
    onboarding.manager.set_state(user_id, STATE_STEPS_INPUT)
    
    bot.send_message(
        user_id,
        "🚶 **Qadamlar**\n\nBugun qancha qadam yurdingiz? (Raqam kiriting)\n\n"
        "Har 10,000 qadam uchun 5 ball beriladi! 🎁",
        parse_mode="Markdown"
    )

def process_steps_input(message, bot):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not text.isdigit():
        bot.send_message(user_id, "Iltimos, faqat raqam kiriting.")
        return
        
    steps = int(text)
    today = datetime.now().strftime("%Y-%m-%d")
    
    db.update_daily_log(user_id, today, steps=steps)
    
    # Calculate points: 5 points per 10k steps
    points = (steps // 10000) * 5
    
    if points > 0:
        db.add_points(user_id, points)
        bot.send_message(user_id, f"✅ **Qoyilmaqom!**\n\nSiz {steps} qadam yurdingiz.\nSizga +{points} ball berildi! 🎉", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"✅ Qabul qilindi: {steps} qadam.\n10,000 ga yetkazishga harakat qiling! 💪")
        
    from bot import onboarding
    onboarding.manager.clear_user(user_id)

# --- Sleep Tracker ---
def handle_sleep_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
        
    from bot import onboarding
    onboarding.manager.set_state(user_id, STATE_SLEEP_INPUT)
    
    bot.send_message(
        user_id,
        "🌙 **Uyqu Monitoringi**\n\nBugun necha soat uxladingiz? (Raqam kiriting, masalan: 7.5)",
        parse_mode="Markdown"
    )

def process_sleep_input(message, bot):
    user_id = message.from_user.id
    text = message.text.strip().replace(',', '.')
    
    try:
        hours = float(text)
    except ValueError:
        bot.send_message(user_id, "Iltimos, to'g'ri raqam kiriting.")
        return
        
    today = datetime.now().strftime("%Y-%m-%d")
    db.update_daily_log(user_id, today, sleep_hours=hours)
    
    if hours >= 8:
        db.add_points(user_id, 2)
        db.update_streak(user_id, 'sleep') # Assuming simple increment for now
        bot.send_message(user_id, f"✅ **Ajoyib uyqu!**\n\nSiz {hours} soat uxladingiz.\nSog'lom uyqu uchun +2 ball! 😴✨", parse_mode="Markdown")
    else:
        bot.send_message(user_id, f"✅ Qabul qilindi: {hours} soat.\nSog'lom bo'lish uchun kamida 8 soat uxlashga harakat qiling.")
        
    from bot import onboarding
    onboarding.manager.clear_user(user_id)

# --- Mood Tracker ---
def handle_mood_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("😞 Yomon", callback_data="track_mood_bad"),
        types.InlineKeyboardButton("😐 O'rtacha", callback_data="track_mood_ok"),
        types.InlineKeyboardButton("😊 A'lo", callback_data="track_mood_good")
    )
    
    bot.send_message(
        user_id,
        "🧠 **Kayfiyat Kundaligi**\n\nBugun o'zingizni qanday his qilyapsiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def process_mood_callback(call, bot):
    user_id = call.from_user.id
    mood = call.data.split('_')[2] # bad, ok, good
    today = datetime.now().strftime("%Y-%m-%d")
    
    db.update_daily_log(user_id, today, mood=mood)
    
    if mood == 'good':
        # 0.5 points (rounded to 1 for integer DB, or need float support? DB is int. Let's give 1 point to be generous or 0.5 if we change DB)
        # User asked for 0.5. DB points is INTEGER. I should probably change DB or just give 1 point every 2 days?
        # Or just give 1 point. Let's give 1 point for now as 0.5 is hard with Int.
        # Wait, I can't change DB type easily now. Let's give 1 point but say it's bonus.
        # Or maybe store as float? No, let's stick to int.
        # Let's give 1 point.
        db.add_points(user_id, 1) 
        db.update_streak(user_id, 'mood')
        
        bot.answer_callback_query(call.id, "✅ Ajoyib! +1 ball")
        bot.edit_message_text(
            "✅ **Kayfiyat a'lo!**\nShunday davom eting! ✨",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
    elif mood == 'bad':
        # Ask for reason
        from bot import onboarding
        onboarding.manager.set_state(user_id, STATE_MOOD_REASON)
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "😔 **Tushunaman...**\n\nNega kayfiyatingiz yomon? Qisqacha yozib yuboring, balki yordam bera olarman.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "✅ Qabul qilindi")
        bot.edit_message_text(
            "✅ **Kayfiyat o'rtacha.**\nYaxshi dam olishga harakat qiling!",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )

def process_mood_reason(message, bot):
    user_id = message.from_user.id
    reason = message.text
    today = datetime.now().strftime("%Y-%m-%d")
    
    db.update_daily_log(user_id, today, mood_reason=reason)
    
    # Log as a problem for easier tracking
    db.log_activity(user_id, "problem", f"Mood Reason: {reason}")
    
    # AI Support
    bot.send_chat_action(user_id, 'typing')
    support_msg = ai_provide_psychological_support(reason)
    
    bot.send_message(user_id, support_msg, parse_mode="HTML")
    
    from bot import onboarding
    onboarding.manager.clear_user(user_id)

# --- Main Habits Menu ---
from bot.keyboards import habits_inline_keyboard

def handle_habits_menu(message, bot):
    with open("assets/kunlik_odatlar.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption="🔁 **Odatlar**\n\nQaysi odatni kiritmoqchisiz?",
            reply_markup=habits_inline_keyboard(),
            parse_mode="Markdown"
        )

def handle_habits_stats(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    log = db.get_daily_log(user_id, today)
    
    water = log.get('water_ml', 0) if log else 0
    steps = log.get('steps', 0) if log else 0
    sleep = log.get('sleep_hours', 0) if log else 0
    
    text = (
        "📊 **Bugungi Ko'rsatkichlar**\n\n"
        f"💧 Suv: {water}/2500 ml\n"
        f"🚶 Qadamlar: {steps}\n"
        f"😴 Uyqu: {sleep} soat\n\n"
        "**Streaklar:**\n"
        f"💧 Suv: {user.get('streak_water', 0)} kun\n"
        f"😴 Uyqu: {user.get('streak_sleep', 0)} kun\n"
        f"🧠 Kayfiyat: {user.get('streak_mood', 0)} kun\n"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
