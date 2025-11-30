from telebot import types
from core.db import db

def handle_challenges_menu(message, bot):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔥 Kunlik Chellenj", callback_data="challenge_daily"),
        types.InlineKeyboardButton("📅 Haftalik Chellenj", callback_data="challenge_weekly"),
        types.InlineKeyboardButton("🏆 Reyting (Leaderboard)", callback_data="challenge_leaderboard")
    )
    bot.send_message(
        message.chat.id,
        "⚔️ **Chellenjlar va Musobaqalar**\n\nO'zingizni sinab ko'ring va ballar yig'ing!",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def handle_daily_challenge(call, bot):
    # Static challenge for MVP
    text = (
        "🔥 **Bugungi Chellenj: 100 ta O'tirib-turish (Squats)**\n\n"
        "Bajarib bo'lgach, 'Bajardim' tugmasini bosing.\n"
        "Mukofot: +10 ball"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Bajardim (+10 ball)", callback_data="challenge_complete_daily"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

def complete_challenge(call, bot, points):
    user_id = call.from_user.id
    db.update_points(user_id, points)
    bot.answer_callback_query(call.id, f"🎉 Tabriklaymiz! +{points} ball")
    bot.edit_message_text(
        f"✅ **Chellenj bajarildi!**\nSizga +{points} ball berildi.\nErtaga yangi chellenj kuting!",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

def show_leaderboard(call, bot):
    # Get top 10 users by points
    # Need to add get_leaderboard to db first, but for now simulate or use raw query
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, yasha_points FROM users ORDER BY yasha_points DESC LIMIT 10")
    leaders = cursor.fetchall()
    conn.close()
    
    text = "🏆 **O'zbekiston Reytingi (TOP 10)**\n\n"
    for i, (name, points) in enumerate(leaders, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        clean_name = name if name else "Foydalanuvchi"
        text += f"{medal} {clean_name} — {points} ball\n"
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
