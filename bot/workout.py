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
    
    from core.utils import safe_split_text, strip_html
    
    # Header is now included in ai_generate_workout response
    full_text = plan
    
    chunks = safe_split_text(full_text)
    
    for chunk in chunks:
        try:
            bot.send_message(user_id, chunk, parse_mode="HTML")
        except Exception:
            # Fallback to plain text (stripped) if HTML fails
            bot.send_message(user_id, strip_html(chunk))

from bot.premium import require_premium

@require_premium
def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (Monthly Menu System)"""
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # 1. Check if user already has an active menu link
    # ACTIVE LINK CHECK DISABLED FOR DEBUGGING
    # active_link = db.get_user_menu_link(user_id)
    # if active_link:
    #     show_daily_menu(bot, user_id, active_link)
    #     return

    # 2. Build Profile Key
    # Key format: gender;goal;activity;age_band
    age = user.get('age', 25)
    age_band = "18-25"
    if age:
        if age > 45: age_band = "46+"
        elif age > 35: age_band = "36-45"
        elif age > 25: age_band = "26-35"
    
    profile_key = f"{user.get('gender')};{user.get('goal')};{user.get('activity_level')};{user.get('allergies')};{age_band}".lower()
    
    # 3. Check for existing Template
    existing_template = db.get_menu_template(profile_key)
    
    if existing_template:
        # FORCE REFRESH: Delete the old template so we can save new valid AI data
        print(f"DEBUG: Deleting old template {profile_key} to replace with fresh AI generation")
        db.delete_menu_template(profile_key)
        
    # 4. Generate New via AI
    msg = bot.send_message(user_id, "🤖 **AI sizning 5 kunlik rejangizni tuzmoqda...**\n\nBu 1 daqiqa vaqt olishi mumkin. Sabr qiling ⏳", parse_mode="Markdown")
    
    try:
        from core.ai import ai_generate_monthly_menu_json
        import json
        
        data = ai_generate_monthly_menu_json(user)
        
        if not data:
            bot.delete_message(user_id, msg.message_id)
            bot.send_message(user_id, "❌ AI xatolik berdi yoki limit tugadi. Iltimos, keyinroq urinib ko'ring.")
            return

        # Save Template
        template_id = db.create_menu_template(
            profile_key,
            json.dumps(data['menu']),
            json.dumps(data['shopping_list'])
        )
        
        # Link User
        db.create_user_menu_link(user_id, template_id)
        
        bot.delete_message(user_id, msg.message_id)
        bot.send_message(user_id, "✅ **Reja tayyor!** Endi har kuni shu yerdan ko'rishingiz mumkin.")
        
        # Show Day 1
        new_link = db.get_user_menu_link(user_id)
        show_daily_menu(bot, user_id, new_link)
            
    except Exception as e:
        print(f"ERROR in generate_ai_meal: {e}")
        bot.send_message(user_id, f"❌ Xatolik: {str(e)[:100]}")

def show_daily_menu(bot, user_id, link_data):
    """Render the menu for specific day index"""
    import json
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    day_idx = link_data['current_day_index']
    menu_list = json.loads(link_data['menu_json'])
    
    # Safe usage
    if day_idx < 1: day_idx = 1
    if day_idx > len(menu_list): day_idx = len(menu_list)
    
    # Find day data (assuming standard array index = day-1)
    day_data = None
    if 0 <= day_idx-1 < len(menu_list):
        day_data = menu_list[day_idx-1]
    
    if not day_data:
        bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
        return

    # Format Message
    txt = f"📅 **{day_data.get('day', day_idx)}-KUN MENYUSI**\n\n"
    txt += f"🍳 **Nonushta:**\n{day_data.get('breakfast', '-')}\n\n"
    txt += f"🥗 **Tushlik:**\n{day_data.get('lunch', '-')}\n\n"
    txt += f"🍲 **Kechki ovqat:**\n{day_data.get('dinner', '-')}\n\n"
    if day_data.get('snack'):
        txt += f"🍏 **Snack:**\n{day_data.get('snack')}"
        
    # Navigation Buttons
    markup = InlineKeyboardMarkup()
    btns = []
    if day_idx > 1:
        btns.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"menu_prev_{day_idx}"))
    if day_idx < len(menu_list):
        btns.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"menu_next_{day_idx}"))
        
    markup.row(*btns)
    markup.row(InlineKeyboardButton("🛒 Shopping List", callback_data="menu_shopping"))
    
    bot.send_message(user_id, txt, parse_mode="Markdown", reply_markup=markup)
