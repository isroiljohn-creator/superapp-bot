from telebot import types
from core.db import db

from bot.keyboards import challenges_inline_keyboard

def handle_challenges_menu(message, bot):
    with open("assets/chellenjlar.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption="🔥 <b>Chellenjlar bo'limi</b>\n\nChellendjlarda qatnashing <b>YASHA coinlar</b> to'plang va ularni obunaga almashtiring\n\n<b>Leaderboard</b> menyusida boshqa foydalanuvchilar bilan bellashing👇🏻",
            reply_markup=challenges_inline_keyboard(),
            parse_mode="HTML"
        )

def handle_weekly_challenge(message, bot):
    text = (
        "📆 **Haftalik Chellenj**\n\n"
        "Vazifa: 5 kun davomida barcha odatlarni (suv, uyqu) to'liq bajarish.\n"
        "Mukofot: +50 ball\n\n"
        "Boshlash uchun shunchaki odatlarni belgilab boring!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def handle_monthly_challenge(message, bot):
    text = (
        "🗓 **Oylik Chellenj**\n\n"
        "Vazifa: 30 kun davomida 100,000 qadam yurish.\n"
        "Mukofot: +200 ball va 'Yasha Walker' nishoni.\n\n"
        "Hozircha qadamlar hisobi qo'lda kiritiladi."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def handle_friends_challenge(message, bot):
    text = (
        "👥 **Do'stlar Chellenji**\n\n"
        "Tez kunda: Do'stingizni taklif qiling va kim ko'p ball yig'ishini sinang!\n"
        "Hozircha do'stlaringizga botni ulashing."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def show_leaderboard_message(message, bot):
    leaders = db.get_top_users(limit=10)
    
    text = "🏆 **O'zbekiston Reytingi (TOP 10)**\n\n"
    for i, (name, points) in enumerate(leaders, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        clean_name = name if name else "Foydalanuvchi"
        text += f"{medal} {clean_name} — {points or 0} coin\n"
        
    bot.send_message(message.chat.id, text, parse_mode="HTML")

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
    db.add_points(user_id, points)
    bot.answer_callback_query(call.id, f"🎉 Tabriklaymiz! +{points} ball")
    bot.edit_message_text(
        f"✅ **Chellenj bajarildi!**\nSizga +{points} ball berildi.\nErtaga yangi chellenj kuting!",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

def show_leaderboard(call, bot):
    leaders = db.get_top_users(limit=10)
    
    text = "🏆 **O'zbekiston Reytingi (TOP 10)**\n\n"
    for i, (name, points) in enumerate(leaders, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        clean_name = name if name else "Foydalanuvchi"
        text += f"{medal} {clean_name} — {points or 0} ball\n"
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")
