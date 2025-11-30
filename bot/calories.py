import json
from telebot import types
from core.db import db
from core.ai import analyze_food_image
from datetime import datetime

# State for calorie photo
STATE_CALORIE_PHOTO = 10

def handle_calorie_button(message, bot, onboarding_manager):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    # Check premium
    is_premium = False
    if user and user.get('premium_until'):
        try:
            premium_until = datetime.fromisoformat(user['premium_until'])
            if premium_until > datetime.now():
                is_premium = True
        except:
            pass
            
    if not is_premium:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 Premium olish", callback_data="buy_premium"))
        bot.send_message(
            user_id,
            "🔒 **Bu funksiya faqat Premium foydalanuvchilar uchun.**\n\n"
            "Premium obuna orqali siz ovqat rasmini yuborib, uning kaloriyasini aniqlashingiz mumkin.",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    # Set state and ask for photo
    onboarding_manager.set_state(user_id, STATE_CALORIE_PHOTO)
    bot.send_message(user_id, "📸 **Ovqat rasmini yuboring.**\n\nMen uni tahlil qilib, kaloriyasini hisoblab beraman.", parse_mode="Markdown")

def handle_food_photo(message, bot, onboarding_manager):
    user_id = message.from_user.id
    
    if onboarding_manager.get_state(user_id) != STATE_CALORIE_PHOTO:
        return

    if not message.photo:
        bot.send_message(user_id, "❌ Iltimos, faqat rasm yuboring.")
        return

    status_msg = bot.send_message(user_id, "⏳ **Tahlil qilinmoqda...**", parse_mode="Markdown")
    
    try:
        # Download photo
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Analyze
        json_result = analyze_food_image(downloaded_file)
        
        if not json_result:
            bot.edit_message_text("❌ Tizimda xatolik yuz berdi. Keyinroq urinib ko'ring.", user_id, status_msg.message_id)
            onboarding_manager.set_state(user_id, 0) # Reset state
            return
            
        try:
            data = json.loads(json_result)
        except json.JSONDecodeError:
            bot.edit_message_text("❌ Noto'g'ri formatdagi javob olindi.", user_id, status_msg.message_id)
            onboarding_manager.set_state(user_id, 0)
            return
            
        if "error" in data:
            bot.edit_message_text("❌ Rasm noto‘g‘ri yoki ovqat aniqlanmadi. Qayta urinib ko‘ring.", user_id, status_msg.message_id)
            # Keep state to allow retry
            return

        # Format output
        items_text = ""
        for item in data.get("items", []):
            items_text += f"• {item.get('name')} — {item.get('grams')} g → {item.get('calories')} kcal\n"
            
        total_calories = data.get("total_calories", 0)
        
        response_text = (
            f"🍽 <b>Kaloriya hisobi:</b>\n\n"
            f"{items_text}\n"
            f"<b>Jami:</b> {total_calories} kcal"
        )
        
        bot.edit_message_text(response_text, user_id, status_msg.message_id, parse_mode="HTML")
        
        # Log to DB
        db.log_calorie_check(user_id, total_calories, json_result)
        
        # Reset state
        onboarding_manager.set_state(user_id, 0)
        
    except Exception as e:
        print(f"ERROR in handle_food_photo: {e}")
        bot.edit_message_text("❌ Xatolik yuz berdi.", user_id, status_msg.message_id)
        onboarding_manager.set_state(user_id, 0)
