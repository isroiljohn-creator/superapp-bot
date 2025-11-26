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
    
    if user_id is None:
        user_id = message.from_user.id
        
    lang = db.get_language(user_id)
    
    if not db.is_premium(user_id):
        # Free user -> Template
        plan = get_template_workout(user_id, lang) # Need to update templates to support lang
        bot.send_message(user_id, plan)
        return

    # Premium -> AI
    msg = bot.send_message(user_id, get_text("generating_plan", lang))
    
    user_data = db.get_user(user_id)
    # Pass language to AI
    plan = ai_generate_workout(user_data, lang=lang) 
    
    bot.edit_message_text(plan, user_id, msg.message_id) # Removed parse_mode="Markdown"

def generate_ai_meal(message, bot, user_id=None):
                bot.send_message(user_id, chunk,parse_mode="HTML")
            except Exception:
                bot.send_message(user_id, chunk)
    else:
        try:
            bot.send_message(user_id, full_text, parse_mode="HTML")
        except Exception:
            bot.send_message(user_id, full_text)
