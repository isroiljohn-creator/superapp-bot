import os
from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

def handle_feedback_start(message, bot):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, "Fikringizni yozing:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_feedback, bot)

def process_feedback(message, bot):
    user_id = message.from_user.id
    text = message.text
    
    # If user cancels or sends a command
    if text.startswith("/"):
        bot.send_message(user_id, "Bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    # Save to DB
    db.add_feedback(user_id, text)
    
    # Notify User
    bot.send_message(user_id, "✅ Rahmat! Fikringiz qabul qilindi va jamoamizga yuborildi.", reply_markup=main_menu_keyboard())
    
    # Forward to Admin
    if ADMIN_ID:
        user = db.get_user(user_id)
        user_name = user['name'] if user else "Unknown"
        admin_msg = (
            f"🆕 **Yangi feedback keldi!**\n"
            f"👤 Foydalanuvchi: {user_name} (ID: {user_id})\n"
            f"📝 Matn:\n{text}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to forward feedback to admin: {e}")

def register_handlers(bot):
    pass # Implicitly handled via menu

