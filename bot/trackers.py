from telebot import types
from core.db import db

# --- Water Tracker ---
def handle_water_tracker(message, bot):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💧 250ml ichdim (+1 ball)", callback_data="track_water_250"))
    
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
    
    bot.answer_callback_query(call.id, "✅ Qabul qilindi! +1 ball")
    bot.edit_message_text(
        "✅ **Ajoyib!** Suv ichishda davom eting. 💧",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# --- Sleep Tracker ---
def handle_sleep_tracker(message, bot):
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
    
    bot.answer_callback_query(call.id, f"✅ Qabul qilindi! +{points} ball")
    bot.edit_message_text(
        f"✅ **Uyqu qayd etildi!**\nSizga +{points} ball berildi.",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# --- Mood Tracker ---
def handle_mood_tracker(message, bot):
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
    
    bot.answer_callback_query(call.id, "✅ Qabul qilindi! +2 ball")
    bot.edit_message_text(
        "✅ **Kayfiyat qayd etildi!**\nHar doim ijobiy bo'ling! ✨",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# --- Main Habits Menu ---
def handle_habits_menu(message, bot):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💧 Suvni belgilash", callback_data="menu_habit_water"),
        types.InlineKeyboardButton("🌙 Uyquni kiritish", callback_data="menu_habit_sleep"),
        types.InlineKeyboardButton("🧠 Kayfiyatni belgilash", callback_data="menu_habit_mood")
    )
    bot.send_message(
        message.chat.id,
        "📋 **Odatlar va Trackerlar**\n\nNimani qayd qilmoqchisiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
