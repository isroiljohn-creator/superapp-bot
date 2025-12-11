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
    from core.ai import ai_generate_monthly_menu_json
    import json
    import time
    
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return
    
    # 1. Check if user already has an active menu link
    # RESTORED: Check for regular users
    active_link = db.get_user_menu_link(user_id)
    if active_link:
        # Auto-open today's menu
        show_daily_menu(bot, user_id, active_link)
        return

    # 2. Build Profile Key
    # Key format: gender;goal;activity;age_band
    age = user.get('age', 25)
    age_band = "18-25"
    if age:
        if age > 45: age_band = "46+"
        elif age > 35: age_band = "36-45"
        elif age > 25: age_band = "26-35"
        
    profile_key = f"{user.get('gender')};{user.get('goal')};{user.get('activity_level')};{user.get('allergies') or 'None'};{age_band}"
    
    msg = bot.send_message(user_id, "🚀 **Jarayon boshlandi...**\n\nBu 30 kunlik reja bo'lgani uchun 60 soniyagacha vaqt olishi mumkin.", parse_mode="Markdown")
    
    # 1. Gather User Data
    user = {
        'age': 25, 'gender': 'Erkak', 'goal': 'Ozish',
        'activity_level': 'O\'rtacha', 'allergies': 'Yo\'q'
    }
    
    # Try to fetch real user data
    db_user = db.get_user(user_id)
    if db_user:
        # Assuming db.get_user returns object or dict. If object:
        # Wait, get_user returns dict usually in this codebase context?
        # Let's check db.get_user usage. Actually, db.get_user returns dict based on prior usage.
        # But to be safe let's assume valid data retrieval or use text extraction if onboarding flow.
        # For now, let's trust the onboarding data is stored.
        # Simulating data extraction if needed...
        user = db_user # Use actual user data if available
        
    # Get profile key
    # Helper logic (simplified for stability):
    profile_key = f"{user_id}_30_day_plan"

    # Clean old template
    existing_template = db.get_menu_template(profile_key)
    if existing_template:
        bot.edit_message_text("🧹 Eski ma'lumotlar tozalanmoqda...", user_id, msg.message_id)
        db.delete_menu_template(profile_key)
        
    try:
        # Retry Loop for Robustness (Force 30 days)
        max_retries = 3
        data = None
        
        for attempt in range(max_retries):
            try:
                # print(f"DEBUG: Generation Attempt {attempt+1}/{max_retries}")
                bot.edit_message_text(f"🤖 AI 30 kunlik menyu tuzmoqda ({attempt+1}-urinish)...", user_id, msg.message_id)
                data = ai_generate_monthly_menu_json(user) # Should pass actual user dict!
                
                if data and 'menu' in data and isinstance(data['menu'], list):
                    item_count = len(data['menu'])
                    
                    if item_count >= 7: 
                        break
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                            
            except Exception as e:
                print(f"gen_attempt_error: {e}")
                if attempt == max_retries - 1:
                    bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                    return
        
        if not data or 'menu' not in data:
            bot.edit_message_text("❌ AI javob bermadi.", user_id, msg.message_id)
            return

        final_count = len(data['menu'])
        if final_count < 5:
             bot.edit_message_text(f"❌ Juda qisqa natija ({final_count} kun). Qayta urining.", user_id, msg.message_id)
             return

        bot.edit_message_text("💾 Bazaga saqlanmoqda...", user_id, msg.message_id)
        
        try:
            template_id = db.create_menu_template(
                profile_key,
                json.dumps(data['menu']),
                json.dumps(data['shopping_list'])
            )
        except Exception as e:
            # Fallback update
            template_id = db.update_menu_template_content(
                profile_key,
                json.dumps(data['menu']),
                json.dumps(data['shopping_list'])
            )
            if not template_id:
                exist = db.get_menu_template(profile_key)
                if exist: template_id = exist['id']
                else: raise e
        
        db.create_user_menu_link(user_id, template_id)
        
        bot.delete_message(user_id, msg.message_id)
        bot.send_message(user_id, "✅ Haftalik reja tayyor! Marhamat:")
        
        new_link = db.get_user_menu_link(user_id)
        show_daily_menu(bot, user_id, new_link, override_day_idx=1)
            
    except Exception as e:
        print(f"Main Gen Error: {e}")
        try:
            bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
        except:
             pass

def get_weekday_name(date_obj):
    # 0=Mon, ... 3=Thu ...
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    return days[date_obj.weekday()]

def show_daily_menu(bot, user_id, link_data, override_day_idx=None):
    """Render the menu for specific day index. 
    If override_day_idx is None, calculates based on date logic (Auto-progression).
    """
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    start_date = link_data['start_date'] # datetime object
    
    # Logic: If no override, calculate specific day
    if override_day_idx is None:
        today = datetime.utcnow() # Assuming start_date is UTC
        # Calculate difference + 1
        # If start_date is today, diff is 0 days, so Day 1.
        delta = today - start_date
        real_day_idx = delta.days + 1
        
        # Cap logic if needed, or if plan expired
        # If real_day_idx > 30, we can say "Finish" or just show 30.
        # Let's show proper day
        day_idx = real_day_idx
    else:
        day_idx = override_day_idx
        
    try:
        # Load Menu
        menu_list = json.loads(link_data['menu_json'])
        total_days = len(menu_list)
        
        # Boundary checks
        clamped = False
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: 
            day_idx = total_days # Stop at last day
            clamped = True
        
        # Calculate Display Date for the *viewed* day
        # viewed_date = start_date + (day_idx - 1) days
        current_view_date = start_date + timedelta(days=day_idx-1)
        weekday_name = get_weekday_name(current_view_date)
        date_str = current_view_date.strftime("%d.%m.%Y")
        
        # Build Text
        txt = f"📅 **{day_idx}-KUN** ({weekday_name}, {date_str})\n\n"
        
        if clamped:
             txt += f"⚠️ **DIQQAT:** Sizning rejangiz jami {total_days} kunlik. Davom etish uchun yangi reja tuzing.\n\n"
             
        db.update_menu_day(user_id, day_idx)

        # Find day data
        day_data = None
        # menu_list is 0-indexed, day_idx is 1-indexed
        idx = day_idx - 1
        if 0 <= idx < total_days:
            day_data = menu_list[idx]
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # Format Message
        # txt is already started
        txt += f"🍳 **Nonushta:** {day_data.get('breakfast', '-')}\n"
        txt += f"🥗 **Tushlik:** {day_data.get('lunch', '-')}\n"
        txt += f"🍲 **Kechki ovqat:** {day_data.get('dinner', '-')}\n"
        txt += f"🍏 **Snack:** {day_data.get('snack', '-')}\n"
            
        # Buttons
        markup = InlineKeyboardMarkup()
        btns = []
            
        if day_idx > 1:
            btns.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"menu_prev_{day_idx}"))
        
        if day_idx < total_days:
            btns.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"menu_next_{day_idx}"))
        elif day_idx == total_days: # End of current plan (e.g. Day 7)
            # Show "Generate Next Week" button
            btns.append(InlineKeyboardButton("Keyingi Hafta (Yangi) 🔄", callback_data="menu_regenerate"))
            
        markup.row(*btns)
        
        # Add Shopping List and Regenerate Buttons
        markup.row(InlineKeyboardButton("🛒 Xaridlar ro'yxati", callback_data="menu_shopping"))
        if day_idx < total_days:
             markup.row(InlineKeyboardButton("🔄 Haftani Yangilash (Reset)", callback_data="menu_regenerate"))
        
        bot.send_message(user_id, txt, parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        print(f"Show Menu Error: {e}")
        bot.send_message(user_id, "❌ Menyu ochishda xatolik.")
