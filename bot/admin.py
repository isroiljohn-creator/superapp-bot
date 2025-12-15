import os
from telebot import types
import time
from core.db import db
from core.content import content_manager
from dotenv import load_dotenv
from core.utils import safe_handler

from core.config import ADMIN_IDS
print(f"DEBUG: Loaded ADMIN_IDS: {ADMIN_IDS}")

# Globals
BROADCAST_STOP = False
BATCH_SIZE = 50

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
            types.KeyboardButton("👨‍💻 Dasturchi")
        )
        bot.send_message(message.chat.id, "👨‍💼 **Admin Panel**", reply_markup=markup, parse_mode="Markdown")
        
    # Register sub handlers
    register_subscription_handlers(bot)
    register_content_handlers(bot)

    @bot.message_handler(commands=['test_ai'])
    @safe_handler(bot)
    def admin_test_ai(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "🤖 AI tekshirilmoqda...")
        
        import google.generativeai as genai
        import os
        
        report = "🤖 <b>AI Test Report:</b>\n\n"
        
        # 1. Check Key
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            report += "❌ <b>Key:</b> Missing!\n"
            bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")
            return
        
        try:
            genai.configure(api_key=key)
            report += "✅ <b>Config:</b> Success\n"
        except Exception as e:
            report += f"❌ <b>Config:</b> {e}\n"
            bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")
            return

        # 2. Test Models
        models = ['gemini-2.5-flash', 'gemini-1.5-flash']
        
        for m_name in models:
            report += f"\nTesting <b>{m_name}</b>:\n"
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content("Hello", request_options={'timeout': 10})
                if response.text:
                    report += "✅ <b>Success!</b>\n"
                else:
                    report += "⚠️ <b>Empty Response</b>\n"
            except Exception as e:
                report += f"❌ <b>Error:</b> {e}\n"
        
        bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="HTML")

    @bot.message_handler(commands=['check_limit'])
    @safe_handler(bot)
    def admin_check_limit(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "⏳ Limit tekshirilmoqda...")
        
        import google.generativeai as genai
        import os
        from core.ai import AI_USAGE_STATS
        
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            bot.edit_message_text("❌ API Key topilmadi.", message.chat.id, msg.message_id)
            return

        # 1. Live Test (Quota Check)
        status_text = ""
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Try a very short generation
            model.generate_content("Test", request_options={'timeout': 5})
            status_text = "✅ <b>AI Ishlayapti</b> (Limit bor)"
        except Exception as e:
            if "429" in str(e):
                status_text = "❌ <b>LIMIT TUGAGAN</b> (Quota Exceeded)"
            else:
                status_text = f"⚠️ <b>Xatolik:</b> {str(e)[:50]}..."

        # 2. Format Stats
        stats_text = (
            f"\n\n📊 <b>Ishlatilgan Limitlar (Restartdan beri):</b>\n"
            f"🏋️‍♂️ Mashqlar: {AI_USAGE_STATS['workout']}\n"
            f"🥗 Menyular: {AI_USAGE_STATS['meal']}\n"
            f"💬 Chat: {AI_USAGE_STATS['chat']}\n"
            f"👁 Vision: {AI_USAGE_STATS['vision']}\n"
            f"🛒 Shopping: {AI_USAGE_STATS['shopping']}\n"
            f"🆘 Support: {AI_USAGE_STATS['support']}\n"
            f"❌ Xatoliklar: {AI_USAGE_STATS['errors']}\n"
            f"-------------------\n"
            f"🔥 <b>Jami So'rovlar: {AI_USAGE_STATS['total_requests']}</b>"
        )
        
        full_text = status_text + stats_text
        bot.edit_message_text(full_text, message.chat.id, msg.message_id, parse_mode="HTML")

    @bot.message_handler(commands=['test_full'])
    @safe_handler(bot)
    def admin_test_full(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(message.chat.id, "🧪 To'liq test boshlandi (Fallback bilan)...")
        
        from core.ai import ask_gemini
        
        prompt = "Siz dietologsiz. 3 kunlik menu tuzing."
        
        try:
            # Use ask_gemini which has the fallback logic (2.5 -> 1.5 -> Pro)
            response_text = ask_gemini("Siz yordamchisiz.", prompt)
            
            if response_text:
                bot.edit_message_text(f"✅ **Success!**\nLength: {len(response_text)}\n\nPreview: {response_text[:100]}...", message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("⚠️ **Empty Response from ask_gemini**", message.chat.id, msg.message_id)
                
        except Exception as e:
            # This catches the "All AI models failed" exception
            bot.edit_message_text(f"❌ **Fallback Failed:** {e}", message.chat.id, msg.message_id)

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
            
            # Translations
            # Translations
            gender_map = {
                "male": "Erkak",
                "female": "Ayol",
                None: "Ro'yxatdan o'tmagan"
            }
            goal_map = {
                "weight_loss": "Vazn tashlash 🔻",
                "muscle_gain": "Vazn olish 🔺",
                "health": "Vaznni ushlab turish ❤️",
                None: "Ro'yxatdan o'tmagan"
            }

            # Dynamic formatting for gender
            gender_text = ""
            for k, v in gender_stats.items():
                # Handle None key or string "None"
                if k == "None": k = None
                label = gender_map.get(k, k if k else "Ro'yxatdan o'tmagan")
                gender_text += f"- {label}: {v}\n"
            if not gender_text: gender_text = "Ma'lumot yo'q"

            # Dynamic formatting for goal
            goal_text = ""
            for k, v in goal_stats.items():
                if k == "None": k = None
                label = goal_map.get(k, k if k else "Ro'yxatdan o'tmagan")
                goal_text += f"- {label}: {v}\n"
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
                f"- Faol: {stats.get('activity', {}).get('active', 0)}\n"
                f"- Atlet: {stats.get('activity', {}).get('athlete', 0)}\n\n"
                f"🔗 <b>Manbalar (UTM):</b>\n"
            )
            
            # UTM Stats logic (quick aggregation)
            # This should ideally be in db.get_stats(), but for MVP I'll fetch here or update db.py
            # Let's update db.py to include 'utm' in get_stats() 
            # OR just do it dynamically here if we trust get_stats returns raw dict.
            # Assuming db.get_stats() needs update.
            # Let's verify what db.get_stats() returns.
            
            utm_stats = stats.get('utm', {})
            for k, v in utm_stats.items():
                if k == "None": k = "Organic/Unknown"
                text += f"- {k}: {v}\n"
                
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            
        except Exception as e:
            import traceback
            print(f"ERROR in admin_stats: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")

    # --- CALLBACK BRIDGES FOR DEV MENU ---
    
    @bot.callback_query_handler(func=lambda call: call.data == "admin_analytics_btn")
    def admin_analytics_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 
                 # Show technical analytics (different from Statistika)
                 stats = db.get_stats()
                 import datetime
                 
                 text = (
                     "📊 <b>Technical Analytics</b>\n\n"
                     f"🤖 Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                     f"👥 Total: {stats.get('total', 0)}\n"
                     f"✅ Active: {stats.get('active', 0)}\n"
                     f"💎 Premium: {stats.get('premium', 0)}\n\n"
                     "<b>Top UTM Sources:</b>\n"
                 )
                 
                 utm_stats = stats.get('utm', {})
                 for k, v in list(utm_stats.items())[:5]:
                     source = k if k else "Organic"
                     text += f"- {source}: {v}\n"
                 
                 bot.send_message(call.message.chat.id, text, parse_mode="HTML")
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error analytics: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik")

    @bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_btn")
    def admin_broadcast_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 # Create a pseudo-message object for admin_broadcast_start
                 class PseudoMessage:
                     def __init__(self, chat_id, from_user):
                         self.chat = type('obj', (object,), {'id': chat_id})
                         self.from_user = from_user
                 
                 pseudo_msg = PseudoMessage(call.message.chat.id, call.from_user)
                 admin_broadcast_start(pseudo_msg)
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error broadcast: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik")
             
    @bot.callback_query_handler(func=lambda call: call.data == "admin_backup_btn")
    def admin_backup_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 
                 # Railway doesn't have pg_dump, show manual backup instructions
                 text = (
                     "📦 <b>Database Backup</b>\n\n"
                     "<b>Avtomatik backup:</b>\n"
                     "Har kuni 03:00 da avtomatik backup yaratiladi.\n\n"
                     "<b>Qo'lda backup:</b>\n"
                     "1. Railway dashboard → Data → Export\n"
                     "2. Yoki pg_dump local ishlatish:\n"
                     "<code>pg_dump $DATABASE_URL > backup.sql</code>\n\n"
                     "⚠️ Railway containerida pg_dump o'rnatilmagan."
                 )
                 bot.send_message(call.message.chat.id, text, parse_mode="HTML")
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error backup: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik")
             
    # Helper function for flags interface (defined early for scope)
    def show_flags_interface(chat_id):
        """Helper to display flags interface - works for both commands and callbacks"""
        flags = db.get_all_feature_flags()
        
        text = "🚩 <b>Feature Flags</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        
        for f in flags:
            status = "✅ ON" if f['enabled'] else "🔴 OFF"
            if f['rollout_percent'] > 0 and f['rollout_percent'] < 100:
                status += f" ({f['rollout_percent']}%)"
                
            text += f"▪️ <b>{f['key']}</b>: {status}\n"
            markup.add(types.InlineKeyboardButton(f"{f['key']} : {status}", callback_data=f"flag_edit_{f['key']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Yangi Flag", callback_data="flag_new"))
        markup.add(types.InlineKeyboardButton("🔄 Yangilash", callback_data="flag_refresh"))
        
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_flags_btn")
    def admin_flags_callback(call):
        try:
            if call.from_user.id in ADMIN_IDS:
                 bot.answer_callback_query(call.id)
                 # Call the helper function with chat_id
                 show_flags_interface(call.message.chat.id)
            else:
                 bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
        except Exception as e:
            print(f"Callback Error admin_flags: {e}")
            import traceback
            traceback.print_exc()
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")

    @bot.message_handler(func=lambda message: "Foydalanuvchilar ro‘yxati" in message.text)
    def admin_user_list(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        
        show_user_list_page(message.chat.id, 1, bot)

    def show_user_list_page(chat_id, page, bot, message_id=None):
        try:
            PAGE_SIZE = 10  # Reduced for more detailed view
            users, total_count = db.get_users_paginated(page, PAGE_SIZE)
            
            if not users:
                text = "👥 Foydalanuvchilar topilmadi."
                if message_id:
                    bot.edit_message_text(text, chat_id, message_id)
                else:
                    bot.send_message(chat_id, text)
                return

            total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
            
            text = f"👥 <b>Foydalanuvchilar</b> (Jami: {total_count})\nSahifa: {page}/{total_pages}\n\n"
            
            for i, user in enumerate(users, 1):
                uid = user['telegram_id']
                name = user['full_name'] or "N/A"
                username = user['username']
                phone = user['phone'] or "N/A"
                goal = user['goal'] or "N/A"
                gender = user['gender'] or "N/A"
                age = user['age'] or "N/A"
                height = user['height'] or "N/A"
                weight = user['weight'] or "N/A"
                activity = user['activity_level'] or "N/A"
                
                # Translations
                goal_map = {
                    "weight_loss": "Vazn tashlash 🔻",
                    "muscle_gain": "Vazn olish 🔺",
                    "health": "Vazn saqlash ❤️",
                    "N/A": "-"
                }
                gender_map = {"male": "👨 Erkak", "female": "👩 Ayol", "N/A": "-"}
                activity_map = {
                    "sedentary": "Kam harakatli",
                    "light": "Yengil faol",
                    "active": "Faol",
                    "athlete": "Atlet",
                    "N/A": "-"
                }
                
                formatted_goal = goal_map.get(goal, goal)
                formatted_gender = gender_map.get(gender, gender)
                formatted_activity = activity_map.get(activity, activity)

                # Premium check
                is_prem = ""
                if user.get('premium_until'):
                    from datetime import datetime
                    if user['premium_until'] > datetime.now():
                        is_prem = " 💎 Premium"
                
                display_name = f"@{username}" if username else name
                
                # Compact but comprehensive display
                text += f"<b>{i}. {display_name}</b>{is_prem}\n"
                text += f"   🆔 ID: <code>{uid}</code>\n"
                text += f"   📱 Tel: {phone}\n"
                text += f"   🎯 Maqsad: {formatted_goal}\n"
                text += f"   {formatted_gender} | {age} yosh | {height}cm / {weight}kg\n"
                text += f"   🏃 Faollik: {formatted_activity}\n\n"
            
            # Pagination + Search Buttons
            markup = types.InlineKeyboardMarkup()
            row = []
            if page > 1:
                row.append(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_users_page_{page-1}"))
            if page < total_pages:
                row.append(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"admin_users_page_{page+1}"))
            
            if row:
                markup.row(*row)
            
            # Add ID Search button
            markup.add(types.InlineKeyboardButton("🔍 ID bo'yicha qidirish", callback_data="admin_search_user_id"))
            
            if message_id:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
                
        except Exception as e:
            print(f"Error in user list: {e}")
            import traceback
            traceback.print_exc()
            error_text = f"❌ Xatolik: {str(e)[:100]}"
            if message_id:
                bot.send_message(chat_id, error_text)
            else:
                bot.send_message(chat_id, error_text)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_users_page_"))
    def handle_user_pagination(call):
        if call.from_user.id not in ADMIN_IDS:
            return
        
        from core.utils import parse_callback
        parts = parse_callback(call.data, prefix="admin_users_page_", min_parts=4)
        
        if not parts:
            bot.answer_callback_query(call.id, "Xatolik")
            return

        try:
            page = int(parts[3])
            show_user_list_page(call.message.chat.id, page, bot, call.message.message_id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Pagination error: {e}")
            bot.answer_callback_query(call.id, "Xatolik yuz berdi")
    
    @bot.callback_query_handler(func=lambda call: call.data == "admin_search_user_id")
    def handle_search_user_id(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🔍 <b>Foydalanuvchini ID bo'yicha qidirish</b>\n\nTelegram ID ni kiriting:",
            parse_mode="HTML",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_user_id_search, bot)
    
    def process_user_id_search(message, bot):
        """Handle ID search input"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        try:
            user_id = int(message.text.strip())
            user = db.get_user(user_id)
            
            if not user:
                bot.send_message(message.chat.id, f"❌ Foydalanuvchi ID <code>{user_id}</code> topilmadi.", parse_mode="HTML")
                return
            
            # Display full user profile
            name = user.get('full_name', 'N/A')
            username = user.get('username', 'N/A')
            phone = user.get('phone', 'N/A')
            goal = user.get('goal', 'N/A')
            gender = user.get('gender', 'N/A')
            age = user.get('age', 'N/A')
            height = user.get('height', 'N/A')
            weight = user.get('weight', 'N/A')
            activity = user.get('activity_level', 'N/A')
            premium_until = user.get('premium_until')
            
            # Translations
            goal_map = {"weight_loss": "Vazn tashlash", "muscle_gain": "Vazn olish", "health": "Vazn saqlash", "N/A": "-"}
            gender_map = {"male": "Erkak", "female": "Ayol", "N/A": "-"}
            activity_map = {"sedentary": "Kam harakatli", "light": "Yengil faol", "active": "Faol", "athlete": "Atlet", "N/A": "-"}
            
            premium_status = "Yo'q"
            if premium_until:
                from datetime import datetime
                if premium_until > datetime.now():
                    premium_status = f"✅ {premium_until.strftime('%Y-%m-%d')}"
            
            text = (
                f"👤 <b>Foydalanuvchi profili</b>\n\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"👤 Ism: {name}\n"
                f"📝 Username: @{username if username != 'N/A' else '-'}\n"
                f"📱 Telefon: {phone}\n\n"
                f"<b>Profil ma'lumotlari:</b>\n"
                f"🎯 Maqsad: {goal_map.get(goal, goal)}\n"
                f"👥 Jins: {gender_map.get(gender, gender)}\n"
                f"🎂 Yosh: {age} yosh\n"
                f"📏 Bo'y: {height} cm\n"
                f"⚖️ Vazn: {weight} kg\n"
                f"🏃 Faollik: {activity_map.get(activity, activity)}\n\n"
                f"💎 Premium: {premium_status}"
            )
            
            bot.send_message(message.chat.id, text, parse_mode="HTML")
            
        except ValueError:
            bot.send_message(message.chat.id, "❌ Noto'g'ri format. Faqat raqam kiriting.")
        except Exception as e:
            print(f"Search error: {e}")
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)[:100]}")

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
    def admin_broadcast_simple(message):
        """Simple broadcast - just send to all users"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        print(f"DEBUG: Simple broadcast by {message.from_user.id}")
        try:
            msg = bot.send_message(
                message.chat.id, 
                "📨 <b>Umumiy xabar</b>\n\nBarcha foydalanuvchilarga xabar yuboring:\n(matn, rasm, video)", 
                reply_markup=types.ForceReply(),
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, process_broadcast, bot, "all")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
    
    # Advanced broadcast with segment options (for Developer menu)
    def admin_broadcast_start(message):
        """Advanced broadcast - with segment selection"""
        if message.from_user.id not in ADMIN_IDS:
            return
        
        print(f"DEBUG: Advanced broadcast by {message.from_user.id}")
        try:
            # Show segment selection
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👥 Barcha foydalanuvchilar", callback_data="broadcast_all"))
            markup.add(types.InlineKeyboardButton("💎 Premium foydalanuvchilar", callback_data="broadcast_premium"))
            markup.add(types.InlineKeyboardButton("🆓 Bepul foydalanuvchilar", callback_data="broadcast_free"))
            
            bot.send_message(
                message.chat.id,
                "📢 <b>Broadcast</b>\n\nQaysi segmentga xabar yubormoqchisiz?",
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
    
    # Broadcast segment selection callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith("broadcast_"))
    def handle_broadcast_segment(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        segment = call.data.replace("broadcast_", "")  # all, premium, or free
        bot.answer_callback_query(call.id)
        
        msg = bot.send_message(
            call.message.chat.id,
            f"📤 Xabarni yuboring ({segment} segment uchun):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_broadcast, bot, segment)

    @bot.message_handler(func=lambda message: "Segment xabar" in message.text)
    def admin_segment_start(message):
        if message.from_user.id not in ADMIN_IDS:
            return
            
        markup = types.InlineKeyboardMarkup()
        # Gender
        markup.row(
            types.InlineKeyboardButton("👨 Erkaklar", callback_data="seg_gender_male"),
            types.InlineKeyboardButton("👩 Ayollar", callback_data="seg_gender_female")
        )
        # Plan Status
        markup.row(
            types.InlineKeyboardButton("💎 Premium", callback_data="seg_premium_True"),
            types.InlineKeyboardButton("👤 Bepul", callback_data="seg_premium_False")
        )
        # Goals
        markup.add(types.InlineKeyboardButton("🔻 Vazn tashlash", callback_data="seg_goal_weight_loss"))
        markup.add(types.InlineKeyboardButton("🔺 Vazn olish", callback_data="seg_goal_muscle_gain"))
        markup.add(types.InlineKeyboardButton("❤️ Vaznni ushlab turish", callback_data="seg_goal_health"))
        
        # Activity
        markup.row(
            types.InlineKeyboardButton("🪑 Kam harakat", callback_data="seg_activity_sedentary"),
            types.InlineKeyboardButton("🏃 O'rtacha", callback_data="seg_activity_moderate")
        )
        markup.add(types.InlineKeyboardButton("🔥 Faol / Atlet", callback_data="seg_activity_athlete"))
        
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

import threading

def process_broadcast(message, bot, segment):
    # Wrapper to run broadcast in background
    thread = threading.Thread(target=_broadcast_worker, args=(message, bot, segment))
    thread.daemon = True # Daemonize to not block shutdown if stuck
    thread.start()
    bot.send_message(message.chat.id, "🚀 Xabar yuborish fonda boshlandi. Menyu orqali ishlatishda davom etishingiz mumkin.")

def _broadcast_worker(message, bot, segment):
    """
    Worker function running in a separate thread.
    """
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
                users = db.get_users_by_segment(goal=value)
            elif key == "premium":
                is_prem = (value == "True")
                users = db.get_users_by_segment(is_premium=is_prem)
            elif key == "activity":
                users = db.get_users_by_segment(activity_level=value)
        
        if not users:
            bot.send_message(message.chat.id, "❌ Foydalanuvchilar topilmadi.")
            return

        msg = bot.send_message(message.chat.id, "⏳ Yuborish boshlanmoqda...")
        status_msg_id = msg.message_id
        
        success = 0
        failed = 0
        offset = 0
        start_time = time.time()
        
        photo = None
        if message.content_type == 'photo':
            photo = message.photo[-1].file_id

        # Use batch processing
        target_segment = segment # 'all' or list

        while True:
            if BROADCAST_STOP:
                bot.send_message(message.chat.id, "🛑 Yuborish to'xtatildi!")
                return

            # Fetch batch
            users_batch_data = []
            if target_segment == "all":
                users_batch_data = db.get_active_users_batch(offset=offset, limit=BATCH_SIZE)
            else:
                key, value = target_segment[0], target_segment[1]
                if key == "gender":
                    users_batch_data = db.get_users_by_segment_batch(gender=value, offset=offset, limit=BATCH_SIZE)
                elif key == "goal":
                    users_batch_data = db.get_users_by_segment_batch(goal=value, offset=offset, limit=BATCH_SIZE)
                elif key == "premium":
                    is_prem = (value == "True")
                    users_batch_data = db.get_users_by_segment_batch(is_premium=is_prem, offset=offset, limit=BATCH_SIZE)
                elif key == "activity":
                    users_batch_data = db.get_users_by_segment_batch(activity_level=value, offset=offset, limit=BATCH_SIZE)

            if not users_batch_data:
                break # No more users in this segment or overall
            
            # Process batch
            for user_id in users_batch_data:
                if BROADCAST_STOP:
                    break
                    
                try:
                    if photo:
                        bot.send_photo(user_id, photo, caption=message.caption)
                    else:
                        bot.send_message(user_id, message.text)
                    success += 1
                except Exception as e:
                    # If blocked, mark inactive
                    if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                        db.set_user_active(user_id, False)
                    failed += 1
                    # print(f"Failed to send to {user_id}: {e}")
                
            # Update status every batch
            elapsed = int(time.time() - start_time)
            try:
                bot.edit_message_text(f"⏳ Yuborilmoqda...\n✅: {success}\n❌: {failed}\n⏱: {elapsed}s", message.chat.id, status_msg_id)
            except: pass
            
            offset += BATCH_SIZE
            time.sleep(1) # Sleep between batches to be nice to API limits
            
        bot.send_message(message.chat.id, f"🏁 Tugadi!\n✅ Muvaffaqiyatli: {success}\n❌ Yetib bormadi: {failed}")
        
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
            markup.add(types.InlineKeyboardButton("🔄 Limitni tiklash (0)", callback_data=f"sub_reset_{target_id}"))
            
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_add_") or call.data.startswith("sub_remove_") or call.data.startswith("sub_reset_"))
    def handle_sub_action(call):
        if call.from_user.id not in ADMIN_IDS:
            return
            
        action, target_id = call.data.split("_")[1], int(call.data.split("_")[2])
        
        if action == "reset":
            db.reset_user_ai_limits(target_id)
            bot.answer_callback_query(call.id, "✅ Limitlar 0 ga tushirildi!")
            return
        
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
            # Choose Plan Type
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⭐️ Premium", callback_data=f"sub_plan_premium_{target_id}"))
            markup.add(types.InlineKeyboardButton("👑 VIP", callback_data=f"sub_plan_vip_{target_id}"))
            
            bot.edit_message_text(
                "Qaysi tarifni bermoqchisiz?",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        # STOP LOADING SPINNER
        try:
            bot.answer_callback_query(call.id)
        except: pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sub_plan_"))
    def handle_sub_plan_selection(call):
        # 1. STOP SPINNER IMMEDIATELY
        try:
            bot.answer_callback_query(call.id)
        except: pass
        
        # 2. Check Auth
        if call.from_user.id not in ADMIN_IDS: 
            print(f"DEBUG: Unauthorized access attempt to sub_plan by {call.from_user.id}")
            return
        
        try:
            parts = call.data.split("_")
            plan_type = parts[2] # premium or vip
            target_id = int(parts[3])
            
            msg = bot.send_message(call.message.chat.id, f"<b>{plan_type.upper()}</b> tarifi uchun necha kun qo'shmoqchisiz? (masalan: 30)", parse_mode="HTML", reply_markup=types.ForceReply())
            bot.register_next_step_handler(msg, process_subs_days, bot, target_id, plan_type)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Xatolik: {e}")
            print(f"Sub Plan Select Error: {e}")

    def process_subs_days(message, bot, target_id, plan_type):
        try:
            if not message.text.isdigit():
                bot.send_message(message.chat.id, "❌ Son kiritishingiz kerak.")
                return

            days = int(message.text)
            # Use new tiered setter
            db.set_user_plan(target_id, plan_type, days)
            
            bot.send_message(message.chat.id, f"✅ Foydalanuvchi ({target_id}) ga {days} kun <b>{plan_type.upper()}</b> tarifi qo'shildi.", parse_mode="HTML")
            
            try:
                bot.send_message(target_id, f"🎉 Tabriklaymiz! Admin sizga {days} kunlik **{plan_type.upper()}** obuna sovg'a qildi!", parse_mode="Markdown")
            except:
                pass
                
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {e}")
            print(f"Sub Add Error: {e}")

    @bot.message_handler(commands=['clear_workouts'])
    def admin_clear_workouts_start(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        msg = bot.send_message(
            message.chat.id, 
            "⚠️ <b>DIQQAT!</b>\n\nBu buyruq BARCHA foydalanuvchilarning eski AI mashq rejalarini o'chirib yuboradi.\nUlarga yangi mashqlar kerak bo'lganda qaytadan generatsiya qilishadi.\n\nDavom etish uchun <code>TASDIQLAYMAN</code> deb yozing:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_clear_workouts_confirmation, bot)

    def process_clear_workouts_confirmation(message, bot):
        if message.text == "TASDIQLAYMAN":
            count = db.clear_all_workout_caches()
            bot.send_message(message.chat.id, f"✅ Bajarildi! {count} ta eski mashq rejasi o'chirib yuborildi.")
        else:
            bot.send_message(message.chat.id, "❌ Bekor qilindi. Tasdiqlash kodi noto'g'ri.")

    @bot.message_handler(commands=['gift_all'])
    def admin_gift_all_start(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        # Parse args
        # /gift_all 5
        parts = message.text.split()
        days = 7
        if len(parts) > 1 and parts[1].isdigit():
            days = int(parts[1])
            
        msg = bot.send_message(
            message.chat.id, 
            f"⚠️ **DIQQAT! KATTA OPERATSIYA**\n\nSiz **BARCHA** foydalanuvchilarga {days} kunlik Premium (Trial) bermoqchisiz.\n\nTasdiqlash uchun **TASDIQLAYMAN** deb yozing.",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_gift_all_confirm, bot, days)

    def process_gift_all_confirm(message, bot, days):
        if message.text == "TASDIQLAYMAN":
            status = bot.send_message(message.chat.id, "⏳ Bajarilmoqda... Bu biroz vaqt olishi mumkin.")
            try:
                count = db.gift_premium_to_all(days=days, plan_type="trial")
                bot.edit_message_text(f"✅ Muvaffaqiyatli! {count} ta foydalanuvchiga {days} kunlik Premium berildi.", message.chat.id, status.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, status.message_id)
        else:
            bot.send_message(message.chat.id, "❌ Bekor qilindi.")

def register_content_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "admin_content_btn")
    def admin_content_callback(call):
        if call.from_user.id not in ADMIN_IDS: return
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔍 Qidirish", callback_data="content_search"))
        
        all_content = content_manager.get_all()
        for key in list(all_content.keys())[:5]:
            markup.add(types.InlineKeyboardButton(f"📝 {key}", callback_data=f"content_edit_{key}"))
            
        bot.send_message(call.message.chat.id, "Matnlarni boshqarish. Qidiruvdan foydalaning yoki ro'yxatdan tanlang:", reply_markup=markup)
        bot.answer_callback_query(call.id)

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
        
        msg = bot.send_message(call.message.chat.id, f"📝 <b>{key}</b>\n\nHozirgi matn:\n<pre>{current_val}</pre>\n\nYangi matnni yuboring:", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_content_edit, bot, key)

    def process_content_edit(message, bot, key):
        new_text = message.text
        if not new_text:
            bot.send_message(message.chat.id, "❌ Matn bo'lishi kerak.")
            return
            
        content_manager.update(key, new_text)
        bot.send_message(message.chat.id, "✅ Saqlandi!")

# --- Phase 7: Observability Extensions ---

    @bot.message_handler(commands=['analytics'])
    def admin_analytics_cmd(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        try:
            if hasattr(db, 'get_analytics_summary'):
                stats = db.get_analytics_summary()
                
                text = (
                    "📊 <b>Mini Analytics</b> (24h)\n\n"
                    f"👥 DAU (Active Users): <b>{stats.get('dau', 0)}</b>\n"
                    f"🚨 Error Rate: <b>{stats.get('error_rate_24h', 0)}%</b> ({stats.get('errors_24h', 0)}/{stats.get('total_events_24h', 0)})\n"
                    f"🕒 Server Time: {datetime.datetime.utcnow().strftime('%H:%M')}\n"
                )
            else:
                text = "📊 <b>Analytics</b>\n\nHozircha analytics funksiyasi mavjud emas."
            
            bot.send_message(message.chat.id, text, parse_mode="HTML")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    @bot.message_handler(commands=['flags'])
    def admin_flags_cmd(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        flags = db.get_all_feature_flags()
        
        text = "🚩 <b>Feature Flags</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        
        for f in flags:
            status = "✅ ON" if f['enabled'] else "🔴 OFF"
            if f['rollout_percent'] > 0 and f['rollout_percent'] < 100:
                status += f" ({f['rollout_percent']}%)"
                
            text += f"▪️ <b>{f['key']}</b>: {status}\n"
            markup.add(types.InlineKeyboardButton(f"{f['key']} : {status}", callback_data=f"flag_edit_{f['key']}"))
            
        markup.add(types.InlineKeyboardButton("➕ Yangi Flag", callback_data="flag_new"))
        markup.add(types.InlineKeyboardButton("🔄 Yangilash", callback_data="flag_refresh"))
        
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("flag_"))
    def handle_flag_actions(call):
        if call.from_user.id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Huquq yo'q", show_alert=True)
            return
        
        action = call.data
        
        if action == "flag_refresh":
            bot.answer_callback_query(call.id)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_flags_interface(call.message.chat.id)
            return
            
        # Edit Flag
        if action.startswith("flag_edit_"):
            key = action.replace("flag_edit_", "")
            flag = db.get_feature_flag(key)
            
            text = f"⚙️ <b>{key}</b> sozlamalari:\n"
            text += f"Status: {'✅ Enabled' if flag['enabled'] else '🔴 Disabled'}\n"
            text += f"Rollout: {flag['rollout_percent']}%\n"
            
            markup = types.InlineKeyboardMarkup()
            # Toggle
            toggle_txt = "🔴 O'chirish" if flag['enabled'] else "✅ Yoqish"
            markup.add(types.InlineKeyboardButton(toggle_txt, callback_data=f"flag_toggle_{key}"))
            
            # Rollout
            markup.row(
                types.InlineKeyboardButton("0%", callback_data=f"flag_roll_{key}_0"),
                types.InlineKeyboardButton("10%", callback_data=f"flag_roll_{key}_10"),
                types.InlineKeyboardButton("50%", callback_data=f"flag_roll_{key}_50"),
                types.InlineKeyboardButton("100%", callback_data=f"flag_roll_{key}_100")
            )
            markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="flag_refresh"))
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return

        # Toggle Action
        if action.startswith("flag_toggle_"):
            key = action.replace("flag_toggle_", "")
            flag = db.get_feature_flag(key)
            # Toggle boolean
            new_status = not flag['enabled']
            db.set_feature_flag(key, new_status)
            
            # Refresh view
            # call.data = f"flag_edit_{key}" # check this hack... no, easier to just recall logic
            # Just re-render the edit view
            flag['enabled'] = new_status # Optimistic update for UI
            
            text = f"⚙️ <b>{key}</b> sozlamalari:\n"
            text += f"Status: {'✅ Enabled' if flag['enabled'] else '🔴 Disabled'}\n"
            text += f"Rollout: {flag['rollout_percent']}%\n"
            
            markup = types.InlineKeyboardMarkup()
            toggle_txt = "🔴 O'chirish" if flag['enabled'] else "✅ Yoqish"
            markup.add(types.InlineKeyboardButton(toggle_txt, callback_data=f"flag_toggle_{key}"))
            markup.row(
                 types.InlineKeyboardButton("0%", callback_data=f"flag_roll_{key}_0"),
                 types.InlineKeyboardButton("10%", callback_data=f"flag_roll_{key}_10"),
                 types.InlineKeyboardButton("50%", callback_data=f"flag_roll_{key}_50"),
                 types.InlineKeyboardButton("100%", callback_data=f"flag_roll_{key}_100")
            )
            markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="flag_refresh"))
            
            bot.answer_callback_query(call.id, "✅ Yangilandi")
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
            return
            
        # Rollout Action
        if action.startswith("flag_roll_"):
            parts = action.split("_") # flag, roll, key, percent
            # key might contain underscores? logic: flag_roll_{key}_{percent}. 
            # Last part is percent.
            percent = int(parts[-1])
            key = "_".join(parts[2:-1])
            
            flag = db.get_feature_flag(key)
            # Enable if > 0 implicitly? User said "enabled=true bo'lsa rollout ishlaydi".
            # So if we set rollout, we probably want to enable it too, or keep current.
            # Let's just set rollout.
            
            db.set_feature_flag(key, flag['enabled'], percent)
            
            # Re-render
            flag['rollout_percent'] = percent
            text = f"⚙️ <b>{key}</b> sozlamalari:\n"
            text += f"Status: {'✅ Enabled' if flag['enabled'] else '🔴 Disabled'}\n"
            text += f"Rollout: {flag['rollout_percent']}%\n"
            
            markup = types.InlineKeyboardMarkup()
            toggle_txt = "🔴 O'chirish" if flag['enabled'] else "✅ Yoqish"
            markup.add(types.InlineKeyboardButton(toggle_txt, callback_data=f"flag_toggle_{key}"))
            markup.row(
                 types.InlineKeyboardButton("0%", callback_data=f"flag_roll_{key}_0"),
                 types.InlineKeyboardButton("10%", callback_data=f"flag_roll_{key}_10"),
                 types.InlineKeyboardButton("50%", callback_data=f"flag_roll_{key}_50"),
                 types.InlineKeyboardButton("100%", callback_data=f"flag_roll_{key}_100")
            )
            markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="flag_refresh"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['seed'])
    def admin_seed_content(message):
        if message.from_user.id not in ADMIN_IDS: return
        
        defaults = {
            "premium_title": "💎 **Premium Bo'limi**",
            "premium_desc": "Premium imkoniyatlari:\n• Cheksiz AI maslahatlari\n• Foto orqali kaloriya aniqlash\n• Chellenjlarda 2x ball",
            "welcome_message": "Assalomu alaykum! YASHA Fitness Botiga xush kelibsiz.",
            "onboarding_name": "Ismingizni kiriting:",
            "onboarding_age": "Yoshingizni kiriting (faqat raqam):"
        }
        
        count = 0
        for key, value in defaults.items():
            if not content_manager.get(key):
                content_manager.set(key, value)
                count += 1
        
        bot.send_message(message.chat.id, f"✅ {count} ta yangi matn bazaga qo'shildi.")


