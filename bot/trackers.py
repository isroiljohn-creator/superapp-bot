from telebot import types
from core.db import db

# --- Water Tracker ---
def handle_water_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💧 250ml ichdim (+1 coin)", callback_data="track_water_250"))
    
    user = db.get_user(user_id)
    streak = user.get('streak_water', 0)
    
    bot.send_message(
        user_id,
        f"💧 **Suv Balansi**\n\nBugungi maqsadingiz: 2.5 litr\nJoriy streak: {streak} kun 🔥\n\nSuv ichdingizmi? Belgilang:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def process_water_callback(call, bot):
    user_id = call.from_user.id
    db.update_streak(user_id, 'water')
    db.update_points(user_id, 1)
    
    bot.answer_callback_query(call.id, "✅ Qabul qilindi! +1 coin")
    bot.edit_message_text(
        "✅ **Ajoyib!** Suv ichishda davom eting. 💧",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# --- Sleep Tracker ---
def handle_sleep_tracker(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("😴 < 6 soat", callback_data="track_sleep_bad"),
        types.InlineKeyboardButton("🙂 6-7 soat", callback_data="track_sleep_ok"),
        types.InlineKeyboardButton("💪 8+ soat", callback_data="track_sleep_good")
    )
    
    bot.send_message(
        user_id,
        "🌙 **Uyqu Monitoringi**\n\nKecha necha soat uxladingiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def process_sleep_callback(call, bot):
    user_id = call.from_user.id
    data = call.data.split('_')[2] # bad, ok, good
    
    points = 0
    if data == 'good': points = 5
    elif data == 'ok': points = 3
    else: points = 1
    
    db.update_streak(user_id, 'sleep')
    db.update_points(user_id, points)
    
    bot.answer_callback_query(call.id, f"✅ Qabul qilindi! +{points} coin")
    bot.edit_message_text(
        f"✅ **Uyqu qayd etildi!**\nSizga +{points} coin berildi.",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

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
    db.update_streak(user_id, 'mood')
    db.update_points(user_id, 2)
    
    bot.answer_callback_query(call.id, "✅ Qabul qilindi! +2 coin")
    bot.edit_message_text(
        "✅ **Kayfiyat qayd etildi!**\nHar doim ijobiy bo'ling! ✨",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# --- Main Habits Menu ---
from bot.keyboards import habits_inline_keyboard

def handle_habits_menu(message, bot):
    bot.send_message(
        message.chat.id,
        "🔁 **Odatlar**\n\nQaysi odatni kiritmoqchisiz?",
        reply_markup=habits_inline_keyboard(),
        parse_mode="Markdown"
    )

def handle_habits_stats(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    text = (
        "📊 **Odatlar Statistikasi**\n\n"
        f"💧 Suv streaki: {user.get('streak_water', 0)} kun\n"
        f"😴 Uyqu streaki: {user.get('streak_sleep', 0)} kun\n"
        f"🧠 Kayfiyat streaki: {user.get('streak_mood', 0)} kun\n"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
