from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu

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

def generate_ai_workout(message, bot):
    """Generate AI workout plan (for premium users)"""
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

def generate_ai_meal(message, bot):
    """Generate AI meal plan (for premium users)"""
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

    msg = bot.send_message(user_id, "⏳ Siz uchun maxsus ovqatlanish rejasi tuzilmoqda... Biroz kuting.")
    
    # Generate plan
    plan = ai_generate_menu(user)
    
    bot.delete_message(user_id, msg.message_id)
    
    header = "🍏 <b>Sizning Individual Ovqatlanish Rejangiz:</b>\n\n"
    full_text = header + plan
    
    if len(full_text) > 4000:
        chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        for chunk in chunks:
            try:
                bot.send_message(user_id, chunk,parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, chunk)
    else:
        try:
            bot.send_message(user_id, full_text, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, full_text)
