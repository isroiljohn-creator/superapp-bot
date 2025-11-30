from telebot import types
from core.db import db
from core.ai import analyze_food_image, analyze_food_text
from bot import onboarding

# States
STATE_CALORIE_PHOTO = "calorie_photo_upload"
STATE_CALORIE_TEXT = "calorie_text_input"

def show_calorie_menu(message, bot):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📷 Rasm orqali", callback_data="calorie_mode_photo"),
        types.InlineKeyboardButton("📝 Matn orqali", callback_data="calorie_mode_text")
    )
    
    bot.send_message(
        message.chat.id,
        "🍽 **Kaloriya Skaneri**\n\nKaloriyani qanday aniqlamoqchisiz?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

def calorie_mode_callback(call, bot):
    user_id = call.from_user.id
    mode = call.data.split('_')[2]
    
    # Check Limit
    allowed, reason = db.check_calorie_limit(user_id)
    if not allowed:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 Premium olish", callback_data="premium_info"))
        
        bot.send_message(
            user_id,
            "🚫 **Limit tugadi**\n\nKaloriya skaneri Premium paketiga kiradi. Siz bugungi bepul limitdan foydalanib bo‘ldingiz. 💚",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
        return

    if mode == 'photo':
        onboarding.manager.set_state(user_id, STATE_CALORIE_PHOTO)
        bot.send_message(
            user_id,
            "📷 **Rasm yuboring**\n\nOvqatingizni yaqin masofadan, yorug‘likda suratga oling va shu yerga yuboring.",
            parse_mode="Markdown"
        )
    elif mode == 'text':
        onboarding.manager.set_state(user_id, STATE_CALORIE_TEXT)
        bot.send_message(
            user_id,
            "📝 **Ovqatni tasvirlang**\n\nOvqat tarkibi va porsiyasini yozing.\nMasalan: \"200 g qaynatilgan guruch, 150 g tovuq filesi, 1 osh qoshiq yog'\"."
        )
    
    bot.answer_callback_query(call.id)

def handle_calorie_photo(message, bot):
    user_id = message.from_user.id
    
    # Double check limit before processing (to prevent bypass)
    allowed, _ = db.check_calorie_limit(user_id)
    if not allowed:
        bot.send_message(user_id, "🚫 Limit tugadi. Premium oling.")
        return

    status_msg = bot.send_message(user_id, "⏳ **Tahlil qilinmoqda...**", parse_mode="Markdown")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        result = analyze_food_image(downloaded_file)
        
        if result:
            db.increment_calorie_usage(user_id)
            bot.edit_message_text(result, user_id, status_msg.message_id, parse_mode="HTML")
        else:
            send_fallback_message(bot, user_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Photo Handler Error: {e}")
        send_fallback_message(bot, user_id, status_msg.message_id)
    
    onboarding.manager.clear_user(user_id)

def handle_calorie_text(message, bot):
    user_id = message.from_user.id
    
    allowed, _ = db.check_calorie_limit(user_id)
    if not allowed:
        bot.send_message(user_id, "🚫 Limit tugadi. Premium oling.")
        return

    status_msg = bot.send_message(user_id, "⏳ **Hisoblanmoqda...**", parse_mode="Markdown")
    
    try:
        result = analyze_food_text(message.text)
        
        if result:
            db.increment_calorie_usage(user_id)
            bot.edit_message_text(result, user_id, status_msg.message_id, parse_mode="HTML")
        else:
            send_fallback_message(bot, user_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Text Handler Error: {e}")
        send_fallback_message(bot, user_id, status_msg.message_id)
        
    onboarding.manager.clear_user(user_id)

def send_fallback_message(bot, chat_id, message_id=None):
    text = """
❌ AI hozir vaqtincha ishlamayapti.

Ammo taxminiy hisoblash uchun:
– Guruch va makaron: 100 g ≈ 130–150 kcal
– Go‘sht va tovuq: 100 g ≈ 150–200 kcal
– Yog‘: 1 osh qoshiq ≈ 100–120 kcal

Keyingi safar qayta urinib ko‘ring. 🙂
    """
    if message_id:
        bot.edit_message_text(text, chat_id, message_id)
    else:
        bot.send_message(chat_id, text)
