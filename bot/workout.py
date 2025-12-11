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
    
    # 3. Check for Existing TEMPLATE (to reuse AI result)
    # DISABLING TEMPLATE REUSE FOR NOW TO FORCE FRESH 30-DAY GENERATION AS REQUESTED
    # existing_template = db.get_menu_template(profile_key)
    # if existing_template:
    #      ...

    # 4. Generate New via AI
    msg = bot.send_message(user_id, "🚀 **Jarayon boshlandi...**\n\nBu 30 kunlik reja bo'lgani uchun 60 soniyagacha vaqt olishi mumkin.", parse_mode="Markdown")
    
    # Check for existing Template to delete (Clean slate)
    existing_template = db.get_menu_template(profile_key)
    
    if existing_template:
        bot.edit_message_text("🧹 Eski ma'lumotlar tozalanmoqda...", user_id, msg.message_id)
        # print(f"DEBUG: Deleting old template {profile_key}")
        db.delete_menu_template(profile_key)
        
        # Retry Loop for Robustness (Force 30 days)
        max_retries = 3
        data = None
        
        for attempt in range(max_retries):
            try:
                # print(f"DEBUG: Generation Attempt {attempt+1}/{max_retries}")
                data = ai_generate_monthly_menu_json(user)
                
                if data and 'menu' in data and isinstance(data['menu'], list):
                    item_count = len(data['menu'])
                    # print(f"DEBUG: Attempt {attempt+1} got {item_count} days")
                    
                    if item_count >= 25: # Accept if at least 25 days (close enough to 30)
                        break
                    else:
                        print(f"DEBUG: Rejecting incomplete menu ({item_count} items). Retrying...")
                        if attempt < max_retries - 1:
                            time.sleep(2) # Brief cooling
                            continue
                
                # If structure is wrong, retry
            except Exception as e:
                print(f"DEBUG: Attempt {attempt+1} detailed error: {e}")
                if attempt == max_retries - 1:
                    bot.edit_message_text(f"❌ Xatolik yuz berdi: {str(e)[:100]}", user_id, msg.message_id)
                    return
        
        if not data or 'menu' not in data:
            bot.edit_message_text("❌ AI to'liq javob bermadi. Iltimos, qayta urinib ko'ring.", user_id, msg.message_id)
            return

        final_count = len(data['menu'])
        if final_count < 5:
             bot.edit_message_text(f"❌ AI faqat {final_count} kunlik reja tuzdi. Qayta urinib ko'ring.", user_id, msg.message_id)
             return

        bot.edit_message_text("💾 Natijalar bazaga saqlanmoqda...", user_id, msg.message_id)
        
        # Save Template (Upsert Logic)
        try:
            # print(f"DEBUG: Attempting to create new template for {profile_key}")
            template_id = db.create_menu_template(
                profile_key,
                json.dumps(data['menu']),
                json.dumps(data['shopping_list'])
            )
        except Exception as e:
            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                # print(f"DEBUG: Duplicate key found for {profile_key}. Updating existing template...")
                template_id = db.update_menu_template_content(
                    profile_key,
                    json.dumps(data['menu']),
                    json.dumps(data['shopping_list'])
                )
                if not template_id:
                    exist = db.get_menu_template(profile_key)
                    template_id = exist['id']
            else:
                raise e
        
        # Link User
        db.create_user_menu_link(user_id, template_id)
        
        bot.delete_message(user_id, msg.message_id)
        # Markdown asterisks removed to prevent errors
        bot.send_message(user_id, "✅ Reja tayyor! Marhamat:")
        
        # Show Day 1 (Fresh start)
        new_link = db.get_user_menu_link(user_id)
        show_daily_menu(bot, user_id, new_link, override_day_idx=1)
            
    except Exception as e:
        print(f"ERROR in generate_ai_meal: {e}")
        try:
            bot.edit_message_text(f"❌ XATOLIK: {str(e)[:200]}", user_id, msg.message_id)
        except:
            bot.send_message(user_id, f"❌ Xatolik: {str(e)[:200]}")

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

    # Load Menu
    menu_list = json.loads(link_data['menu_json'])
    total_days = len(menu_list)
    
    # Boundary checks
    if day_idx < 1: day_idx = 1
    if day_idx > total_days: day_idx = total_days # Stop at last day
    
    # Calculate Display Date for the *viewed* day
    # viewed_date = start_date + (day_idx - 1) days
    current_view_date = start_date + timedelta(days=day_idx-1)
    weekday_name = get_weekday_name(current_view_date)
    
    # Format Date nicely (e.g. 12-Dek) if needed, but weekday + Day Number is good enough 
    
    # Save current position to DB if navigating?
    # Actually, requirement says "Ertaga kirib 2-kun ochilsin".
    # This implies usually we don't save navigation unless we want to resume navigation?
    # But if we Auto-Progression on entry (override_day_idx=None), then saving user navigation state here
    # is only for "Resume where I left off browsing".
    # Let's update DB `current_day_index` to reflect what is being viewed currently.
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

    # Clean function to remove markdown chars that break telegram
    def clean(t):
        if not t: return "-"
        return str(t).replace("*", "").replace("_", "")

    # Format Message
    txt = f"📅 {day_idx}-KUN ({weekday_name})\n"
    # txt += f"Sanasi: {current_view_date.strftime('%d.%m')}\n\n"
    txt += "\n"
    txt += f"🍳 Nonushta:\n{clean(day_data.get('breakfast', '-'))}\n\n"
    txt += f"🥗 Tushlik:\n{clean(day_data.get('lunch', '-'))}\n\n"
    txt += f"🍲 Kechki ovqat:\n{clean(day_data.get('dinner', '-'))}\n\n"
    if day_data.get('snack'):
        txt += f"🍏 Snack:\n{clean(day_data.get('snack'))}"
        
    # Navigation Buttons
    markup = InlineKeyboardMarkup()
    btns = []
    if day_idx > 1:
        btns.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"menu_prev_{day_idx}"))
    if day_idx < total_days:
        btns.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"menu_next_{day_idx}"))
        
    markup.row(*btns)
    markup.row(InlineKeyboardButton("🛒 Shopping List", callback_data="menu_shopping"))
    
    # Send without parse_mode or with HTML if needed, but plain text is safest for mixed content
    bot.send_message(user_id, txt, reply_markup=markup)
