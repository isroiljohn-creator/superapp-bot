import os
from telebot import types
from core.db import db
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
print(f"DEBUG: Loaded ADMIN_ID: {ADMIN_ID}")

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

    @bot.message_handler(func=lambda message: "Statistika" in message.text and message.from_user.id == ADMIN_ID)
    def admin_stats(message):
        try:
            stats = db.get_stats()
            
            # Safe retrieval with defaults
            total = stats.get('total', 0)
            active = stats.get('active', 0)
            premium = stats.get('premium', 0)
            gender_stats = stats.get('gender', {})
            goal_stats = stats.get('goal', {})
            
            text = (
                f"📊 **Statistika**\n\n"
                f"👥 Jami foydalanuvchilar: {total}\n"
                f"✅ Faol foydalanuvchilar: {active}\n"
                f"💎 Premium foydalanuvchilar: {premium}\n\n"
                f"👨 Erkaklar: {gender_stats.get('male', 0) + gender_stats.get('Erkak', 0)}\n"
                f"👩 Ayollar: {gender_stats.get('female', 0) + gender_stats.get('Ayol', 0)}\n\n"
                f"⚖️ Ozish: {goal_stats.get('weight_loss', 0) + goal_stats.get('Ozish', 0)}\n"
                f"💪 Massa: {goal_stats.get('mass_gain', 0) + goal_stats.get('Massa olish', 0)}\n"
                f"❤️ Sog‘liq: {goal_stats.get('health', 0) + goal_stats.get('Sog‘liqni tiklash', 0)}"
            )
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
            
        except Exception as e:
            print(f"ERROR in admin_stats: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")

    @bot.message_handler(func=lambda message: "Foydalanuvchilar ro‘yxati" in message.text)
    def admin_user_list(message):
        if message.from_user.id != ADMIN_ID:
            print(f"DEBUG: Unauthorized admin access attempt by {message.from_user.id}")
            return
        
        try:
            # Get last 20 users (assuming ID order roughly correlates with time)
            users = db.get_active_users() # Returns list of (id, name)
            
            if not users:
                bot.send_message(message.chat.id, "👥 Foydalanuvchilar topilmadi.")
                return

            # Sort by ID desc to get newest first
            users.sort(key=lambda x: x[0], reverse=True)
            recent_users = users[:20]
            
            text = "👥 Oxirgi 20 ta foydalanuvchi:\n\n"
            for uid, name in recent_users:
                user_data = db.get_user(uid)
                if not user_data:
                    continue
                    
                is_prem = "💎" if db.is_premium(uid) else ""
                phone = user_data.get('phone', 'N/A')
                goal = user_data.get('goal', 'N/A')
                
                # Clean name to avoid issues
                clean_name = name if name else "Noma'lum"
                
                text += f"🆔 {uid} | {clean_name} | 📱 {phone} | {goal} {is_prem}\n"
                
            bot.send_message(message.chat.id, text)
            
        except Exception as e:
            print(f"Error in admin_user_list: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Premium foydalanuvchilar" in message.text)
    def admin_premium_list(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        # This is a bit expensive without a direct DB query, but fine for MVP
        users = db.get_users_by_segment(is_premium=True)
        
        text = f"💎 **Premium Foydalanuvchilar ({len(users)}):**\n\n"
        for uid, name in users[:20]:
            text += f"🆔 `{uid}` | {name}\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: "Referallar" in message.text)
    def admin_referrals(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        top_referrers = db.get_top_referrals(10)
        
        text = "🏷 **TOP 10 Referallar:**\n\n"
        for item in top_referrers:
            text += f"👤 {item['name']} (ID: `{item['id']}`) — {item['count']} ta taklif\n"
            
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    @bot.message_handler(func=lambda message: "Umumiy xabar" in message.text)
    def admin_broadcast_start(message):
        if message.from_user.id != ADMIN_ID:
            return
        
        print(f"DEBUG: Admin broadcast started by {message.from_user.id}")
        try:
            msg = bot.send_message(message.chat.id, "Xabarni yuboring (matn, rasm, video, ovozli xabar):", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_broadcast, bot, "all")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Segment xabar" in message.text)
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

    @bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id == ADMIN_ID)
    def admin_reply_to_user(message):
        """Handle admin replying to a user's feedback"""
        try:
            original_text = message.reply_to_message.text or message.reply_to_message.caption
            if not original_text:
                return
            
            # Extract User ID from the original message text
            # Format expected: "👤 Foydalanuvchi: Name (ID: 12345)"
            import re
            match = re.search(r"\(ID: (\d+)\)", original_text)
            
            if match:
                user_id = int(match.group(1))
                reply_text = message.text or "Rasm/Video"
                
                # Send to user
                try:
                    bot.copy_message(user_id, message.chat.id, message.message_id)
                    bot.reply_to(message, f"✅ Xabar foydalanuvchiga (ID: {user_id}) yuborildi.")
                except Exception as e:
                    bot.reply_to(message, f"❌ Yuborishda xatolik: {e}")
            else:
                bot.reply_to(message, "⚠️ Foydalanuvchi ID si topilmadi. Xabar formatini tekshiring.")
                
        except Exception as e:
            print(f"Error in admin reply: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("seg_"))
    def admin_segment_select(call):
        if call.from_user.id != ADMIN_ID:
            return
            
        segment = call.data.split("_")[1:] # ['gender', 'Erkak'] or ['premium', 'True']
        msg = bot.send_message(call.message.chat.id, f"Tanlangan segment: {segment[0]}={segment[1]}. Xabarni yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_broadcast, bot, segment)

def process_broadcast(message, bot, segment):
    try:
        # Check if user cancelled
        if message.text and message.text.startswith("/"):
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")
            return

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
        
        if not users:
            bot.send_message(message.chat.id, "❌ Foydalanuvchilar topilmadi.")
            return

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
        
    except Exception as e:
        print(f"Error in process_broadcast: {e}")
        try:
            bot.send_message(message.chat.id, f"❌ Xabar yuborishda xatolik: {e}")
        except:
            pass
