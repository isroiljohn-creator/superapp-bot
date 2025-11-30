from datetime import datetime
from telebot import types
from core.db import db
from bot.keyboards import gamification_keyboard, points_menu_keyboard

def handle_points_menu(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    points = user.get('yasha_points', 0)
    
    text = (
        f"🟡 **Yasha Ball**\n\n"
        f"Sizning balingiz: **{points}** ⭐️\n\n"
        "Ballarni qanday ishlash mumkin?\n"
        "• Odatlar (suv, uyqu) → +1-5 ball\n"
        "• Do'stlarni taklif qilish → +10 ball\n"
        "• Chellenjlar → +50 ballgacha"
    )
    
    bot.send_message(message.chat.id, text, reply_markup=points_menu_keyboard(), parse_mode="Markdown")

def handle_my_points(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    points = user.get('yasha_points', 0)
    text = f"📊 **Sizning Ballaringiz:** {points}\n\nDavom eting! 🚀"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def handle_rewards(message, bot):
    text = (
        "🎁 **Mukofotlar**\n\n"
        "• 100 ball = 1 hafta Premium\n"
        "• 500 ball = 1 oy Premium\n"
        "• 1000 ball = Yasha Merch (futbolka/kepka)\n\n"
        "Tez kunda almashish imkoniyati qo'shiladi! ⏳"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def handle_rules(message, bot):
    text = (
        "📜 **Qoidalar**\n\n"
        "1. Har kuni odatlarni belgilang.\n"
        "2. Yolg'on ma'lumot kiritmang.\n"
        "3. Do'stlaringizni taklif qiling.\n"
        "4. Chellenjlarda faol qatnashing.\n\n"
        "Halollik - eng muhim qoida! 🤝"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def handle_tasks(message, bot):
    user_id = message.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    log = db.get_daily_log(user_id, today)
    
    # Check if already checked in
    user = db.get_user(user_id)
    checked_in = user.get('last_checkin') == today
    
    status_icon = "✅" if checked_in else "❌"
    
    text = (
        f"📅 **Bugungi vazifalar ({today}):**\n\n"
        "1) 6-8 stakan suv ichish\n"
        "2) 10-15 daqiqa yurish\n"
        "3) 1 blok mashq bajarish\n\n"
        f"Status: {status_icon}\n\n"
        "Vazifalarni bajargan bo‘lsangiz, tugmani bosing:"
    )
    
    markup = types.InlineKeyboardMarkup()
    if not checked_in:
        markup.add(types.InlineKeyboardButton("✅ Vazifani bajardim (+1 ball)", callback_data="task_done"))
    else:
        markup.add(types.InlineKeyboardButton("✅ Bajarildi", callback_data="task_already_done"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "task_done")
    def handle_task_done(call):
        user_id = call.from_user.id
        today = datetime.now().strftime("%Y-%m-%d")
        user = db.get_user(user_id)
        
        # Double check
        if user.get('last_checkin') == today:
            bot.answer_callback_query(call.id, "Bugun allaqachon vazifani bajargansiz! 🙂", show_alert=True)
            return

        # Award points
        points_to_add = 1
        db.add_points(user_id, points_to_add)
        db.update_user_profile(user_id, last_checkin=today)
        
        # Log daily activity
        db.update_daily_log(user_id, today, workout_done=True)
        
        bot.answer_callback_query(call.id, f"Zo‘r! Bugungi vazifa bajarildi, ball qo‘shildi 🎉")
        
        # Update message
        handle_tasks(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "task_already_done")
    def handle_already_done(call):
        bot.answer_callback_query(call.id, "Bugun allaqachon belgilagansiz, ertaga yana kutamiz 🙂", show_alert=True)

