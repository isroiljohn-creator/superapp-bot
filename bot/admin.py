import os
from telebot import types
from core.db import db
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id != ADMIN_ID:
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("📊 Statistika"),
            types.KeyboardButton("👥 Foydalanuvchilar ro‘yxati"),
            types.KeyboardButton("📨 Umumiy xabar"),
            types.KeyboardButton("🎯 Segment xabar"),
            types.KeyboardButton("💎 Premium foydalanuvchilar"),
            types.KeyboardButton("🏷 Referallar")
        )
        bot.send_message(message.chat.id, "👨‍💼 **Admin Panel**", reply_markup=markup, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "📊 Statistika")
    def admin_stats(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        stats = db.get_stats()
        text = (
            f"📊 **Statistika**\n\n"
            f"👥 Jami foydalanuvchilar: {stats['total']}\n"
            f"✅ Faol foydalanuvchilar: {stats['active']}\n"
            f"💎 Premium foydalanuvchilar: {stats['premium']}\n\n"
            f"👨 Erkaklar: {stats['gender'].get('Erkak', 0)}\n"
            f"👩 Ayollar: {stats['gender'].get('Ayol', 0)}\n\n"
            f"⚖️ Ozish: {stats['goal'].get('Ozish', 0)}\n"
            f"💪 Massa: {stats['goal'].get('Massa olish', 0)}\n"
            f"❤️ Sog‘liq: {stats['goal'].get('Sog‘liqni tiklash', 0)}"
        )
        bot.send_message(message.chat.id, text)

    @bot.message_handler(func=lambda message: message.text == "👥 Foydalanuvchilar ro‘yxati")
    def admin_user_list(message):
        if message.from_user.id != ADMIN_ID:
            return
        
        # Get last 20 users (assuming ID order roughly correlates with time)
        # We need a method in DB for this, or just use get_all_users and slice
        # Since get_all_users returns (id, name), we might need more info.
        # Let's use get_active_users for now or add a specific DB method if needed.
        # For MVP, we'll just list active users.
        users = db.get_active_users() # Returns list of (id, name)
        
        # Sort by ID desc to get newest first
        users.sort(key=lambda x: x[0], reverse=True)
        recent_users = users[:20]
        
        text = "👥 **Oxirgi 20 ta foydalanuvchi:**\n\n"
        for uid, name in recent_users:
            user_data = db.get_user(uid)
            is_prem = "💎" if db.is_premium(uid) else ""
            phone = user_data.get('phone', 'N/A')
            text += f"🆔 `{uid}` | {name} | 📱 {phone} | {user_data.get('goal', 'N/A')} {is_prem}\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "💎 Premium foydalanuvchilar")
    def admin_premium_list(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        # This is a bit expensive without a direct DB query, but fine for MVP
        users = db.get_users_by_segment(is_premium=True)
        
        text = f"💎 **Premium Foydalanuvchilar ({len(users)}):**\n\n"
        for uid, name in users[:20]:
            text += f"🆔 `{uid}` | {name}\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "🏷 Referallar")
    def admin_referrals(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        top_referrers = db.get_top_referrals(10)
        
        text = "🏷 **TOP 10 Referallar:**\n\n"
        for item in top_referrers:
            text += f"👤 {item['name']} (ID: `{item['id']}`) — {item['count']} ta taklif\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: message.text == "📨 Umumiy xabar")
    def admin_broadcast_start(message):
        if message.from_user.id != ADMIN_ID:
            return
        
        msg = bot.send_message(message.chat.id, "Xabarni yuboring (matn, rasm, video, ovozli xabar):", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_broadcast, bot, "all")

    @bot.message_handler(func=lambda message: message.text == "🎯 Segment xabar")
    def admin_segment_start(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👨 Erkaklar", callback_data="seg_gender_Erkak"))
        markup.add(types.InlineKeyboardButton("👩 Ayollar", callback_data="seg_gender_Ayol"))
        markup.add(types.InlineKeyboardButton("⚖️ Ozish", callback_data="seg_goal_Ozish"))
        markup.add(types.InlineKeyboardButton("💪 Massa", callback_data="seg_goal_Massa"))
        markup.add(types.InlineKeyboardButton("💎 Premium", callback_data="seg_premium_True"))
        markup.add(types.InlineKeyboardButton("👤 Oddiy", callback_data="seg_premium_False"))
        
        bot.send_message(message.chat.id, "Segmentni tanlang:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("seg_"))
    def admin_segment_select(call):
        if call.from_user.id != ADMIN_ID:
            return
            
        segment = call.data.split("_")[1:] # ['gender', 'Erkak'] or ['premium', 'True']
        msg = bot.send_message(call.message.chat.id, f"Tanlangan segment: {segment[0]}={segment[1]}. Xabarni yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_broadcast, bot, segment)

def process_broadcast(message, bot, segment):
    users = []
    if segment == "all":
        users = db.get_active_users()
    else:
        key, value = segment[0], segment[1]
        if key == "gender":
            users = db.get_users_by_segment(gender=value)
        elif key == "goal":
            # Simple fuzzy match for goal
            users = db.get_users_by_segment(goal=value)
        elif key == "premium":
            is_prem = (value == "True")
            users = db.get_users_by_segment(is_premium=is_prem)
    
    count = 0
    blocked = 0
    
    status_msg = bot.send_message(message.chat.id, f"🚀 Xabar yuborish boshlandi... (Jami: {len(users)})")
    
    for i, user in enumerate(users):
        try:
            bot.copy_message(user[0], message.chat.id, message.message_id)
            count += 1
        except Exception as e:
            # If blocked, mark inactive
            if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                db.set_user_active(user[0], False)
                blocked += 1
            # print(f"Failed to send to {user[0]}: {e}")
        
        # Update status every 20 users
        if i % 20 == 0:
            try:
                bot.edit_message_text(f"🚀 Yuborilmoqda... {i}/{len(users)}", message.chat.id, status_msg.message_id)
            except:
                pass
    
    bot.send_message(message.chat.id, f"✅ Xabar yuborish yakunlandi.\n\n✅ Muvaffaqiyatli: {count}\n🚫 Bloklaganlar: {blocked}")
