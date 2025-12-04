import os
from telebot import types
from core.db import db
from dotenv import load_dotenv

load_dotenv()
MAIN_ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
ADMIN_IDS = [MAIN_ADMIN_ID, 1392501306]
print(f"DEBUG: Loaded ADMIN_IDS: {ADMIN_IDS}")

def register_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMIN_IDS:
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("📊 Statistika"),
            types.KeyboardButton("👥 Foydalanuvchilar ro‘yxati"),
            types.KeyboardButton("📨 Umumiy xabar"),
            types.KeyboardButton("🎯 Segment xabar"),
            types.KeyboardButton("💎 Premium foydalanuvchilar"),
            types.KeyboardButton("🏷 Referallar"),
            types.KeyboardButton("💳 Obunalar"),
            types.KeyboardButton("✍️ Matnlarni tahrirlash")
        )
        bot.send_message(message.chat.id, "👨‍💼 **Admin Panel**", reply_markup=markup, parse_mode="Markdown")
        
    # Register sub handlers
    register_subscription_handlers(bot)

    @bot.message_handler(commands=['resetdb'])
    def admin_reset_db(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        msg = bot.send_message(message.chat.id, "⚠️ **DIQQAT!**\n\nBu buyruq butun bazani o'chirib yuboradi (foydalanuvchilar, loglar, hamma narsa). \n\nDavom etish uchun 'TASDIQLAYMAN' deb yozing.", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_reset_db_confirm, bot)

    def process_reset_db_confirm(message, bot):
        if message.text == "TASDIQLAYMAN":
            try:
                db.reset_db()
                bot.send_message(message.chat.id, "✅ Baza muvaffaqiyatli tozalandi va qayta yaratildi.")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
        else:
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")

    @bot.message_handler(func=lambda message: "Statistika" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_stats(message):
        try:
            stats = db.get_stats()
            
            # Safe retrieval with defaults
            total = stats.get('total', 0)
            active = stats.get('active', 0)
            premium = stats.get('premium', 0)
            gender_stats = stats.get('gender', {})
            goal_stats = stats.get('goal', {})
            
            # Dynamic formatting for gender
            gender_text = ""
            for k, v in gender_stats.items():
                gender_text += f"- {k}: {v}\n"
            if not gender_text: gender_text = "Ma'lumot yo'q"

            # Dynamic formatting for goal
            goal_text = ""
            for k, v in goal_stats.items():
                goal_text += f"- {k}: {v}\n"
            if not goal_text: goal_text = "Ma'lumot yo'q"
            
            text = (
                f"📊 <b>Statistika</b>\n\n"
                f"👥 Jami foydalanuvchilar: {total}\n"
                f"✅ Faol foydalanuvchilar: {active}\n"
                f"💎 Premium foydalanuvchilar: {premium}\n\n"
                f"👨👩 <b>Jins bo'yicha:</b>\n{gender_text}\n"
                f"🎯 <b>Maqsad bo'yicha:</b>\n{goal_text}\n"
                f"🏃 <b>Faollik:</b>\n"
                f"- Kam harakat: {stats.get('activity', {}).get('sedentary', 0)}\n"
                f"- Yengil: {stats.get('activity', {}).get('light', 0)}\n"
                f"- O'rtacha: {stats.get('activity', {}).get('moderate', 0)}\n"
                f"- Faol: {stats.get('activity', {}).get('active', 0)}\n"
                f"- Atlet: {stats.get('activity', {}).get('athlete', 0)}"
            )
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            
        except Exception as e:
            print(f"ERROR in admin_stats: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")

    @bot.message_handler(func=lambda message: "Foydalanuvchilar ro‘yxati" in message.text)
    def admin_user_list(message):
        if message.from_user.id not in ADMIN_IDS:
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
            
            text = "👥 <b>Oxirgi 20 ta foydalanuvchi:</b>\n\n"
            for uid, name, username in recent_users:
                user_data = db.get_user(uid)
                if not user_data:
                    continue
                    
                is_prem = "💎" if db.is_premium(uid) else ""
                phone = user_data.get('phone', 'N/A')
                goal = user_data.get('goal', 'N/A')
                
                # Prioritize username, then name, then fallback
                display_name = f"@{username}" if username else (name if name else "Noma'lum")
                
                # Clean name to avoid issues
                import html
                safe_name = html.escape(display_name)
                
                text += f"🆔 <code>{uid}</code> | {safe_name} | 📱 {phone} | {goal} {is_prem}\n"
                
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            
        except Exception as e:
            print(f"Error in admin_user_list: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Premium foydalanuvchilar" in message.text)
    def admin_premium_list(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        # This is a bit expensive without a direct DB query, but fine for MVP
        users = db.get_users_by_segment(is_premium=True)
        
        text = f"💎 <b>Premium Foydalanuvchilar:</b>\n\n"
        for uid, name, username in users[:20]:
            # Prioritize username, then name, then fallback
            display_name = f"@{username}" if username else (name if name else "Noma'lum")
            
            # Escape HTML in name
            import html
            safe_name = html.escape(display_name)
            
            text += f"🆔 <code>{uid}</code> | {safe_name}\n"
            
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(func=lambda message: "Referallar" in message.text)
    def admin_referrals(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        top_referrers = db.get_top_referrals(10)
        
        text = "🏷 <b>TOP 10 Referallar:</b>\n\n"
        for item in top_referrers:
            import html
            safe_name = html.escape(item['name']) if item['name'] else "Noma'lum"
            text += f"👤 {safe_name} (ID: <code>{item['id']}</code>) — {item['count']} ta taklif\n"
            
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(func=lambda message: "Umumiy xabar" in message.text)
    def admin_broadcast_start(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        print(f"DEBUG: Admin broadcast started by {message.from_user.id}")
        try:
            msg = bot.send_message(message.chat.id, "Xabarni yuboring (matn, rasm, video, ovozli xabar):", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_broadcast, bot, "all")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(func=lambda message: "Segment xabar" in message.text)
    def admin_segment_start(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👨 Erkaklar", callback_data="seg_gender_Erkak"))
        markup.add(types.InlineKeyboardButton("👩 Ayollar", callback_data="seg_gender_Ayol"))
        markup.add(types.InlineKeyboardButton("⚖️ Ozish", callback_data="seg_goal_Ozish"))
        markup.add(types.InlineKeyboardButton("💪 Massa", callback_data="seg_goal_Massa"))
        markup.add(types.InlineKeyboardButton("💎 Premium", callback_data="seg_premium_True"))
        markup.add(types.InlineKeyboardButton("👤 Oddiy", callback_data="seg_premium_False"))
        markup.add(types.InlineKeyboardButton("🪑 Kam harakat", callback_data="seg_activity_sedentary"))
        markup.add(types.InlineKeyboardButton("🏃 O'rtacha", callback_data="seg_activity_moderate"))
        markup.add(types.InlineKeyboardButton("🔥 Atlet", callback_data="seg_activity_athlete"))
        
        bot.send_message(message.chat.id, "Segmentni tanlang:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id in ADMIN_IDS)
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
        if call.from_user.id not in ADMIN_IDS:
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
                # Map Uzbek label to DB value
                db_value = "male" if value == "Erkak" else "female"
                users = db.get_users_by_segment(gender=db_value)
            elif key == "goal":
                # Map Uzbek label to DB value
                db_value = "weight_loss" if value == "Ozish" else ("muscle_gain" if value == "Massa" else value)
                users = db.get_users_by_segment(goal=db_value)
            elif key == "premium":
                is_prem = (value == "True")
                users = db.get_users_by_segment(is_premium=is_prem)
            elif key == "activity":
                users = db.get_users_by_segment(activity_level=value)
        
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

# === Subscription Management ===

def register_subscription_handlers(bot):
    @bot.message_handler(func=lambda message: "Obunalar" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_subs_start(message):
        msg = bot.send_message(message.chat.id, "Foydalanuvchi ID raqamini yuboring:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_subs_user_id, bot)

    def process_subs_user_id(message, bot):
        try:
            if not message.text.isdigit():
                bot.send_message(message.chat.id, "❌ ID raqam bo'lishi kerak.")
                return
            
            target_id = int(message.text)
            user = db.get_user(target_id)
            
            if not user:
                bot.send_message(message.chat.id, f"❌ Foydalanuvchi topilmadi: {target_id}")
                return
            
            is_prem = db.is_premium(target_id)
            status = "✅ Premium" if is_prem else "❌ Oddiy"
            until = user.get('premium_until', 'Yo‘q')
            
            text = (
                f"👤 **Foydalanuvchi:** {user.get('full_name', 'Noma’lum')}\n"
                f"🆔 ID: `{target_id}`\n"
                f"💎 Status: {status}\n"
                f"📅 Tugash: {until}\n\n"
                "Amalni tanlang:"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("➕ Obuna qo'shish", callback_data=f"sub_add_{target_id}"))
            markup.add(types.InlineKeyboardButton("➖ Obunani o'chirish", callback_data=f"sub_remove_{target_id}"))
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
    def handle_sub_action(call):
        if call.from_user.id not in ADMIN_IDS:
            return
            
        action, target_id = call.data.split("_")[1], int(call.data.split("_")[2])
        
        if action == "remove":
            db.remove_premium(target_id)
            bot.edit_message_text(
                f"✅ Foydalanuvchi ({target_id}) dan Premium olib tashlandi.",
                call.message.chat.id,
                call.message.message_id
            )
            try:
                bot.send_message(target_id, "❌ Sizning Premium obunangiz admin tomonidan bekor qilindi.")
            except:
                pass
                
        elif action == "add":
            msg = bot.send_message(call.message.chat.id, f"Necha kun qo'shmoqchisiz? (masalan: 30)", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_subs_days, bot, target_id)

    def process_subs_days(message, bot, target_id):
        try:
            days = int(message.text)
            db.set_premium(target_id, days)
            
            bot.send_message(message.chat.id, f"✅ Foydalanuvchi ({target_id}) ga {days} kun Premium qo'shildi.")
            
            try:
                bot.send_message(target_id, f"🎉 Tabriklaymiz! Admin sizga {days} kunlik Premium obuna sovg'a qildi!")
            except:
                pass
                
        except ValueError:
# === Content Management ===
    from core.content import content_manager

    @bot.message_handler(func=lambda message: "Matnlarni tahrirlash" in message.text and message.from_user.id in ADMIN_IDS)
    def admin_content_start(message):
        # List categories or show keys
        # For simplicity, let's show keys directly or search
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # We can group by category if we had many, but for now list all or search
        markup.add(types.InlineKeyboardButton("🔍 Qidirish", callback_data="content_search"))
        
        # Add some common keys manually or fetch top ones
        all_content = content_manager.get_all()
        for key in list(all_content.keys())[:5]:
            markup.add(types.InlineKeyboardButton(f"📝 {key}", callback_data=f"content_edit_{key}"))
            
        bot.send_message(message.chat.id, "Matnlarni boshqarish. Qidiruvdan foydalaning yoki ro'yxatdan tanlang:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "content_search")
    def admin_content_search_prompt(call):
        if call.from_user.id not in ADMIN_IDS: return
        msg = bot.send_message(call.message.chat.id, "Kalit so'zni kiriting (masalan: welcome):", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_content_search, bot)

    def process_content_search(message, bot):
        query = message.text.lower()
        all_content = content_manager.get_all()
        matches = [k for k in all_content.keys() if query in k.lower()]
        
        if not matches:
            bot.send_message(message.chat.id, "❌ Hech narsa topilmadi.")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key in matches[:10]: # Limit to 10
            markup.add(types.InlineKeyboardButton(f"📝 {key}", callback_data=f"content_edit_{key}"))
            
        bot.send_message(message.chat.id, f"🔍 '{query}' bo'yicha natijalar:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("content_edit_"))
    def admin_content_edit_prompt(call):
        if call.from_user.id not in ADMIN_IDS: return
        key = call.data.replace("content_edit_", "")
        current_val = content_manager.get(key)
        
        text = f"🔑 **Kalit:** `{key}`\n\n📄 **Hozirgi matn:**\n{current_val}\n\n✏️ Yangi matnni yuboring:"
        msg = bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_content_update, bot, key)

    def process_content_update(message, bot, key):
        new_val = message.text
        if new_val.startswith("/"):
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")
            return
            
        if content_manager.set(key, new_val):
            bot.send_message(message.chat.id, f"✅ **{key}** yangilandi!")
        else:
            bot.send_message(message.chat.id, "❌ Saqlashda xatolik bo'ldi.")
