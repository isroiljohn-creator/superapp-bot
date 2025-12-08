from datetime import datetime
from telebot import types
from core.db import db
from bot.keyboards import gamification_keyboard, points_inline_keyboard

def handle_points_menu(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    points = user.get('yasha_points', 0)
    
    text = (
        f"🟡 **Yasha Coin**\n\n"
        f"Sizning balingiz: **{points}** 🟡\n\n"
        "Coinlarni qanday ishlash mumkin?\n"
        "• Odatlar (suv, uyqu) → +1-5 coin\n"
        "• Do'stlarni taklif qilish → +1 coin\n"
        "• Chellenjlar → +50 coingacha"
    )
    
    markup = points_inline_keyboard()
    markup.add(types.InlineKeyboardButton("🔗 Referal havola", callback_data="points_referral"))
    
    # If called from callback, maybe edit message? But for now send new.
    # Actually, if we want to be nice, we can try to edit if it's a callback message.
    # But let's stick to send_message for consistency with other menus unless requested.
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

def handle_referral_link(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    # Generate link if not exists (though db should have it, let's generate on fly if needed)
    # Actually db stores referral_code.
    code = user.get('referral_code')
    if not code:
        code = f"r{user_id}" # Fallback
        
    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start={code}"
    
    text = (
        "🔗 **Sizning referal havolangiz:**\n\n"
        f"`{link}`\n\n"
        "Bu havolani do'stlaringizga yuboring. Ular ro'yxatdan o'tsa, sizga +1 coin beriladi! 🟡"
    )
    
    with open("assets/referal.png", "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption=text, parse_mode="Markdown")

def handle_my_points(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    points = user.get('yasha_points', 0)
    text = f"📊 **Sizning Ballaringiz:** {points}\n\nDavom eting! 🚀"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def handle_rewards(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    points = user.get('points', 0) # Use 'points' not 'yasha_points' as per DB schema
    
    breakdown = db.get_todays_points_breakdown(user_id)
    
    text = (
        f"🎁 **Mukofotlar Marketi**\n\n"
        f"💰 Sizning hisobingiz: **{points} ball**\n\n"
        f"📊 **Bugungi daromad (+{breakdown['total']}):**\n"
        f"💧 Suv: +{breakdown['water']}\n"
        f"🚶 Qadam: +{breakdown['steps']}\n"
        f"😴 Uyqu: +{breakdown['sleep']}\n"
        f"😊 Kayfiyat: +{breakdown['mood']}\n\n"
        "👇 **Ballarni almashtirish:**"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💎 1 Hafta Premium (100 ball)", callback_data="redeem_prem_7"))
    markup.add(types.InlineKeyboardButton("💎 1 Oy Premium (500 ball)", callback_data="redeem_prem_30"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

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

    @bot.callback_query_handler(func=lambda call: call.data.startswith("redeem_"))
    def handle_redeem(call):
        user_id = call.from_user.id
        action = call.data.split("_")[1] # prem
        value = call.data.split("_")[2] # 7 or 30
        
        cost = 0
        days = 0
        
        if action == "prem":
            if value == "7":
                cost = 100
                days = 7
            elif value == "30":
                cost = 500
                days = 30
        
        # Confirm dialog
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_redeem_{cost}_{days}"),
            types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_redeem")
        )
        
        bot.edit_message_text(
            f"❓ **Tasdiqlash**\n\n{days} kunlik Premium uchun {cost} ball sarflanadi.\nRozimisiz?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_redeem_"))
    def process_redeem_confirm(call):
        user_id = call.from_user.id
        cost = int(call.data.split("_")[2])
        days = int(call.data.split("_")[3])
        
        success, msg = db.redeem_points(user_id, cost, "premium_days", days)
        
        if success:
            bot.answer_callback_query(call.id, "Muvaffaqiyatli! 🎉", show_alert=True)
            bot.edit_message_text(
                f"🎉 **Tabriklaymiz!**\n\nSiz {cost} ball evaziga {days} kunlik Premium oldingiz!\n\n/start bosib tekshirishingiz mumkin.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, f"Xatolik: {msg}", show_alert=True)
            # Return to menu
            handle_rewards(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_redeem")
    def process_redeem_cancel(call):
        handle_rewards(call.message, bot)

