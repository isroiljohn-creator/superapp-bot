from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu

def handle_workout_plan(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    msg = bot.send_message(user_id, "⏳ Siz uchun maxsus mashqlar rejasi tuzilmoqda... Biroz kuting.")
    
    # Generate plan
    print(f"DEBUG: Generating workout plan for user {user_id}...")
    plan = ai_generate_workout(user)
    print(f"DEBUG: Plan generated. Length: {len(plan) if plan else 0}")
    
    bot.delete_message(user_id, msg.message_id)
    
    header = "🏋️‍♂️ **Sizning Mashq Rejangiz:**\n\n"
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

def handle_meal_plan(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    msg = bot.send_message(user_id, "⏳ Siz uchun maxsus ovqatlanish rejasi tuzilmoqda... Biroz kuting.")
    
    # Generate plan
    plan = ai_generate_menu(user)
    
    bot.delete_message(user_id, msg.message_id)
    
    header = "🍏 <b>Sizning Ovqatlanish Rejangiz:</b>\n\n"
    full_text = header + plan
    
    if len(full_text) > 4000:
        chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        for chunk in chunks:
            try:
                bot.send_message(user_id, chunk, parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, chunk)
    else:
        try:
            bot.send_message(user_id, full_text, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, full_text)
