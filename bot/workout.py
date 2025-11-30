from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu
from bot.keyboards import plan_inline_keyboard

def handle_plan_menu(message, bot):
    bot.send_message(
        message.chat.id,
        "🏋️ **Mening Rejam**\n\nQaysi reja kerak?",
        reply_markup=plan_inline_keyboard(),
        parse_mode="Markdown"
    )

def handle_workout_plan(message, bot):
    """Entry point for workout plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_workout_template_menu
    show_workout_template_menu(message, bot)

def handle_meal_plan(message, bot):
    """Entry point for meal plans - show template menu"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Show template selection menu
    from bot.templates import show_meal_template_menu
    show_meal_template_menu(message, bot)

def generate_ai_workout(message, bot, user_id=None):
    """Generate AI workout plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # Check premium status
    if not db.is_premium(user_id):
        bot.send_message(
            user_id,
            "⚠️ Individual AI reja faqat Premium foydalanuvchilar uchun mavjud.\n\n"
            "💎 Premium obuna sotib oling va sizga maxsus reja tayyorlanadi!",
            parse_mode="Markdown"
        )
        return

    msg = bot.send_message(user_id, "⏳ Siz uchun maxsus mashqlar rejasi tuzilmoqda... Biroz kuting.")
    
    # Generate plan
    print(f"DEBUG: Generating workout plan for user {user_id}...")
    plan = ai_generate_workout(user)
    print(f"DEBUG: Plan generated. Length: {len(plan) if plan else 0}")
    
    bot.delete_message(user_id, msg.message_id)
    
    header = "🏋️‍♂️ **Sizning Individual Mashq Rejangiz:**\n\n"
    full_text = header + plan
    
    if len(full_text) > 4000:
        # Split into chunks
        chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        for chunk in chunks:
            try:
                bot.send_message(user_id, chunk, parse_mode="HTML")
            except Exception:
                # Fallback to plain text if HTML fails
                bot.send_message(user_id, chunk)
    else:
        try:
            bot.send_message(user_id, full_text, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, full_text)

def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    bot.send_message(user_id, "🤖 **AI Ovqatlanish rejasi tuzilmoqda...**\n\nIltimos, biroz kuting ⏳", parse_mode="Markdown")
    
    prompt = f"""
    Foydalanuvchi ma'lumotlari:
    Yosh: {user.get('age')}
    Jins: {user.get('gender')}
    Bo'y: {user.get('height')}
    Vazn: {user.get('weight')}
    Maqsad: {user.get('goal')}
    Faollik darajasi: {user.get('activity_level')}
    
    Ushbu ma'lumotlar asosida 1 haftalik batafsil ovqatlanish rejasi tuzib ber. 
    Har bir kun uchun ovqatlanish vaqti, taom nomi va miqdorini yoz.
    Javobni O'zbek tilida, chiroyli formatda (Markdown) qaytar.
    """
    
    try:
        response = ai_generate_menu(prompt)
        bot.send_message(user_id, response, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(user_id, "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")
