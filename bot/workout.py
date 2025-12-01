from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu
from bot.keyboards import plan_inline_keyboard
from bot.premium import require_premium

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

@require_premium
def generate_ai_workout(message, bot, user_id=None):
    """Generate AI workout plan (for premium users)"""
    if user_id is None:
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

from bot.premium import require_premium

@require_premium
def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    msg = bot.send_message(user_id, "🤖 **AI Ovqatlanish rejasi tuzilmoqda...**\n\nIltimos, biroz kuting ⏳", parse_mode="Markdown")
    
    try:
        # Pass the user object directly, as ai_generate_menu expects a user profile dict
        response = ai_generate_menu(user)
        
        try:
            bot.delete_message(user_id, msg.message_id)
        except:
            pass
        
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                try:
                    bot.send_message(user_id, chunk, parse_mode="HTML")
                except Exception:
                    bot.send_message(user_id, chunk)
        else:
            bot.send_message(user_id, response, parse_mode="HTML")
            
    except Exception as e:
        print(f"ERROR in generate_ai_meal: {e}")
        bot.send_message(user_id, "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")
