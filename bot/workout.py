import os
from telebot import types
from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu
from bot.keyboards import plan_inline_keyboard
from bot.premium import require_premium
from core.flags import is_flag_enabled
import traceback

# Simple in-memory lock
GENERATION_LOCKS = set()


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
    """Generate AI workout plan (7-Day JSON System)"""
    from core.ai import ai_generate_weekly_workout_json
    import json
    import time
    
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    # 0. Check Limit
    allowed, limit_msg = db.check_ai_gen_limit(user_id, 'workout')
    if not allowed:
        bot.send_message(user_id, limit_msg, parse_mode="Markdown")
        return

    # 0.5 Check Lock
    if user_id in GENERATION_LOCKS:
        bot.send_message(user_id, "⏳ Sabr qiling, reja tuzilmoqda...")
        return
        
    GENERATION_LOCKS.add(user_id)
    try:
        # 1. Check if user already has an active workout link
        active_link = db.get_user_workout_link(user_id)
        if active_link:
            # Auto-open today's workout
            show_daily_workout(bot, user_id, active_link)
            return

        # 2. Build Shared Profile Key (Deduplication)
        # Group users by simple age bands to increase matches
        age = user.get('age', 25)
        age_band = "18-25"
        if age > 45: age_band = "46+"
        elif age > 35: age_band = "36-45"
        elif age > 25: age_band = "26-35"
        
        # Key: workout_v2_Gender_Goal_Activity_AgeBand
        profile_key = f"workout_v2_{user.get('gender')}_{user.get('goal')}_{user.get('activity_level')}_{age_band}".replace(" ", "_").lower()

        # 3. Check for Existing Shared Template
        existing_template = db.get_workout_template(profile_key)
        
        if existing_template:
            bot.send_message(user_id, "💡 Sizga mos tayyor reja topildi! Yuklanmoqda...")
            db.create_user_workout_link(user_id, existing_template['id'])
            
            new_link = db.get_user_workout_link(user_id)
            db.increment_ai_usage(user_id, 'workout') 
            show_daily_workout(bot, user_id, new_link, override_day_idx=1)
            return

        # If no template, generate new
        msg = bot.send_message(user_id, "⏳ Siz uchun 7 kunlik mashg'ulotlar rejasini tuzyapman... Biroz kuting.")
            
        try:
            # [SAFE LOGGING ADDITION]
            try:
                from core.ai_usage_logger import log_ai_usage
                log_ai_usage(bot, user_id, "workout", 2500)
            except: pass

            # Retry Loop for Robustness
            max_retries = 3
            data = None
            
            for attempt in range(max_retries):
                try:
                    try:
                        bot.edit_message_text(f"🧘‍♀️ Siz uchun 7 kunlik mashg'ulotlar rejasini tuzyapman...", user_id, msg.message_id) # Safe edit
                    except: pass
                    
                    # [SMART CONTEXT INJECTION]
                    from core.flags import is_flag_enabled
                    from core.context import get_user_context, get_founder_tone_prompt
                    
                    # Create a copy to not mutate DB object
                    user_ctx = dict(user) 
                    
                    extra_ctx = ""
                    if is_flag_enabled("stateful_ai_context", user_id):
                        extra_ctx += get_user_context(user_id)
                        
                    if is_flag_enabled("founder_tone", user_id):
                        extra_ctx += get_founder_tone_prompt()
                        
                    if extra_ctx:
                        current_goal = user_ctx.get('goal', '')
                        user_ctx['goal'] = f"{current_goal}. {extra_ctx}"
                        
                    data = ai_generate_weekly_workout_json(user_ctx)
                    
                    if data and 'schedule' in data and isinstance(data['schedule'], list):
                        item_count = len(data['schedule'])
                        
                        if item_count >= 5: # Accept at least 5 days
                            break
                        else:
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                                
                except Exception as e:
                    print(f"workout_gen_attempt_error: {e}")
                    if attempt == max_retries - 1:
                        try:
                            bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                        except: pass
                        return
            
            if not data or 'schedule' not in data:
                bot.edit_message_text(f"❌ AI javob bermadi.", user_id, msg.message_id)
                return

            final_count = len(data['schedule'])
            if final_count < 5:
                 bot.edit_message_text(f"❌ Juda qisqa natija ({final_count} kun). Qayta urining.", user_id, msg.message_id)
                 return

            bot.edit_message_text("💾 Bazaga saqlanmoqda...", user_id, msg.message_id)
            
            try:
                template_id = db.create_workout_template(
                    profile_key,
                    json.dumps(data['schedule'])
                )
            except Exception as e:
                # Fallback update
                template_id = db.update_workout_template_content(
                    profile_key,
                    json.dumps(data['schedule'])
                )
                if not template_id:
                    exist = db.get_workout_template(profile_key)
                    if exist: template_id = exist['id']
                    else: raise e
            
            db.create_user_workout_link(user_id, template_id)
            
            bot.delete_message(user_id, msg.message_id)
            bot.send_message(user_id, "✅ Haftalik mashqlar rejasi tayyor! Marhamat:")
            
            new_link = db.get_user_workout_link(user_id)
            db.increment_ai_usage(user_id, 'workout')
            show_daily_workout(bot, user_id, new_link, override_day_idx=1)
                
        except Exception as e:
            print(f"Main Workout Gen Error: {e}")
            try:
                bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
            except:
                 pass
    except Exception as e:
         print(f"Outer Gen Error: {e}")
    finally:
        if user_id in GENERATION_LOCKS:
            GENERATION_LOCKS.remove(user_id)

def show_daily_workout(bot, user_id, link_data, override_day_idx=None):
    """Render the workout for specific day index."""
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    start_date = link_data['start_date']
    day_idx = link_data['current_day_index']
    
    # Safe date parsing
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except:
             try:
                 start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
             except:
                 start_date = datetime.utcnow()

    # Logic: If no override, use DB value. 
    # (Simplified from menu logic, we trust DB or override)
    if override_day_idx is not None:
        day_idx = override_day_idx
        
    try:
        # Load Workout
        schedule = json.loads(link_data['workout_json'])
        total_days = len(schedule)
        
        # Boundary checks
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: 
            day_idx = total_days
        
        db.update_workout_day(user_id, day_idx)

        # Find day data
        day_data = None
        idx = day_idx - 1
        if 0 <= idx < total_days:
            day_data = schedule[idx]
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # Format Message
        # { "day": 1, "focus": "...", "exercises": "..." }
        
        focus_uu = day_data.get('focus', 'Umumiy')
        
        # Helper map to ensure Uzbek (fallback)
        tr_map = {
            "Upper Body": "Yuqori Tana",
            "Lower Body": "Pastki Tana",
            "Full Body": "Butun Tana",
            "Core": "Press / Bel",
            "Cardio": "Kardio",
            "Rest": "Dam olish",
            "Dam olish (Rest)": "Dam olish"
        }
        # If the AI returns English, map it. If it returns Uzbek, keep it.
        final_focus = tr_map.get(focus_uu, focus_uu)
        
        txt = f"🏋️ <b>{day_idx}-KUN REJASI</b> (Jami {total_days} kun)\n"
        txt += f"🎯 <b>Fokus:</b> {final_focus}\n\n"
        
        exercises_text = day_data.get('exercises', '-')
        
        # REST DAY LOGIC
        if "dam" in final_focus.lower() or "rest" in final_focus.lower():
             import random
             variants = [
                 # Variant 1 - Ayb hissini yo'qotish
                 ("😌 <b>Bugun dam</b>\n\n"
                  "Dam olish — bu ortga qaytish emas.\n"
                  "Mushaklar aynan bugun tiklanadi va kuchayadi.\n\n"
                  "Ertaga tanang “rahmat” deydi."),
                 # Variant 2 - Ilmiy + Oddiy
                 ("🧠 <b>Bilasanmi?</b>\n\n"
                  "O‘sish mashq vaqtida emas, dam olishda bo‘ladi.\n"
                  "Bugun tana ishlayapti — sen sezmasang ham."),
                 # Variant 3 - Qisqa, ammo kuchli
                 ("<b>Bugun dam — bu ham rejaga kiradi.</b>\n"
                  "Rejani buzmadik, to‘g‘ri bajaryapmiz ✅")
             ]
             rest_msg = random.choice(variants)
             txt += f"{rest_msg}\n\n"
             # Show original text if meaningful (like stretching), else hide
             if len(exercises_text) > 20 and "tiklanish" not in exercises_text.lower():
                 txt += f"<i>Qo'shimcha: {exercises_text}</i>"
        else:
             # Regular Workout
             txt += f"{exercises_text}"
        
        # [SMART PAYWALL]
        from core.context import get_smart_paywall_cta
        if is_flag_enabled("smart_paywall", user_id):
            cta = get_smart_paywall_cta(user_id)
            if cta: txt += cta
            
        # Buttons
        markup = InlineKeyboardMarkup()
        btns = []
            
        if day_idx > 1:
            btns.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"workout_prev_{day_idx}"))
        
        if day_idx < total_days:
            btns.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"workout_next_{day_idx}"))
            
        markup.row(*btns)
        
        # Regenerate Button
        if day_idx == total_days:
             markup.row(InlineKeyboardButton("🔄 Yangi Reja Tuzish", callback_data="workout_regenerate"))
        else:
             markup.row(InlineKeyboardButton("🔄 Yangilash (Reset)", callback_data="workout_regenerate"))
        
        bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

    except Exception as e:
        print(f"Show Workout Error: {e}")
        bot.send_message(user_id, "❌ Mashqni ochishda xatolik.")

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

    # 0. Check Limit
    allowed, limit_msg = db.check_ai_gen_limit(user_id, 'menu')
    if not allowed:
        bot.send_message(user_id, limit_msg, parse_mode="Markdown")
        return

    # 0.5 Check Lock
    if user_id in GENERATION_LOCKS:
        bot.send_message(user_id, "⏳ Sabr qiling, reja tuzilmoqda...")
        return

    GENERATION_LOCKS.add(user_id)
    try:
    
        # 1. Check if user already has an active menu link
        # RESTORED: Check for regular users
        active_link = db.get_user_menu_link(user_id)
        if active_link:
            # Auto-open today's menu
            show_daily_menu(bot, user_id, active_link)
            return

        # 2. Build Shared Profile Key (Deduplication)
        age = user.get('age', 25)
        age_band = "18-25"
        if age > 45: age_band = "46+"
        elif age > 35: age_band = "36-45"
        elif age > 25: age_band = "26-35"
            
        profile_key = f"menu_v2_{user.get('gender')}_{user.get('goal')}_{user.get('activity_level')}_{user.get('allergies')}_{age_band}".replace(" ", "_").lower()
        
        # 3. Check for Existing Shared Template
        existing_template = db.get_menu_template(profile_key)
        
        if existing_template:
            bot.send_message(user_id, "💡 Sizga mos tayyor menyu topildi! Yuklanmoqda...")
            db.create_user_menu_link(user_id, existing_template['id'])
            
            new_link = db.get_user_menu_link(user_id)
            db.increment_ai_usage(user_id, 'menu')
            show_daily_menu(bot, user_id, new_link, override_day_idx=1)
            return

        # If no template, generate new
        # If no template, generate new
        msg = bot.send_message(user_id, "🚀 **Jarayon boshlandi...**\n\n🥗 Siz uchun 7 kunlik ovqatlanish menyusini tuzyapman...", parse_mode="Markdown")
            
        # [SAFE LOGGING ADDITION]
        try:
            from core.ai_usage_logger import log_ai_usage
            log_ai_usage(bot, user_id, "menu", 2000)
        except: pass
            
        try:
            # Retry Loop for Robustness (Force 30 days)
            max_retries = 3
            data = None
            
            for attempt in range(max_retries):
                try:
                    try:
                        bot.edit_message_text(f"🥗 Siz uchun 7 kunlik ovqatlanish menyusini tuzyapman...", user_id, msg.message_id)
                    except: pass
                    
                    # [SMART CONTEXT INJECTION]
                    from core.flags import is_flag_enabled
                    from core.context import get_user_context, get_founder_tone_prompt
                    
                    user_ctx = dict(user) 
                    extra_ctx = ""
                    if is_flag_enabled("stateful_ai_context", user_id):
                        extra_ctx += get_user_context(user_id)
                    if is_flag_enabled("founder_tone", user_id):
                        extra_ctx += get_founder_tone_prompt()
                        
                    if extra_ctx:
                        user_ctx['goal'] = f"{user_ctx.get('goal','')}. {extra_ctx}"

                    data = ai_generate_monthly_menu_json(user_ctx)
                    
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
                        try:
                            bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, msg.message_id)
                        except: pass
                        return
            
            if not data or 'menu' not in data:
                try:
                    bot.edit_message_text("❌ AI javob bermadi.", user_id, msg.message_id)
                except: pass
                return

            final_count = len(data['menu'])
            if final_count < 5:
                 try:
                    bot.edit_message_text(f"❌ Juda qisqa natija ({final_count} kun). Qayta urining.", user_id, msg.message_id)
                 except: pass
                 return

            try:
                bot.edit_message_text("💾 Bazaga saqlanmoqda...", user_id, msg.message_id)
            except: pass
            
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
            
            try:
                bot.delete_message(user_id, msg.message_id)
            except: pass
            bot.send_message(user_id, "✅ Haftalik reja tayyor! Marhamat:")
            
            new_link = db.get_user_menu_link(user_id)
            db.increment_ai_usage(user_id, 'menu')
            show_daily_menu(bot, user_id, new_link, override_day_idx=1)
                
        except Exception as e:
            print(f"Main Gen Error: {e}")
            try:
                bot.edit_message_text(f"❌ Katta Xatolik: {str(e)[:100]}", user_id, msg.message_id)
            except:
                 pass
    finally:
        if user_id in GENERATION_LOCKS:
            GENERATION_LOCKS.remove(user_id)

def get_weekday_name(date_obj):
    # 0=Mon, ... 3=Thu ...
    days = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    return days[date_obj.weekday()]

def _esc(text):
    """Helper to escape HTML characters"""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def show_daily_menu(bot, user_id, link_data, day_idx=None, meal_type='breakfast'):
    """
    Render a specific meal for a specific day.
    meal_type: 'breakfast', 'lunch', 'dinner', 'snack'
    """
    import json
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    start_date = link_data['start_date']
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            except:
                start_date = datetime.utcnow()
    
    if day_idx is None:
        # Calculate current day based on start date
        today = datetime.utcnow()
        delta = today - start_date
        day_idx = delta.days + 1
    
    try:
        menu_list = json.loads(link_data['menu_json'])
        total_days = len(menu_list)
        
        if day_idx < 1: day_idx = 1
        if day_idx > total_days: day_idx = total_days
        
        # Update current day in DB
        db.update_menu_day(user_id, day_idx)

        idx = day_idx - 1
        day_data = menu_list[idx] if 0 <= idx < total_days else None
        
        if not day_data:
            bot.send_message(user_id, "⚠️ Bu kun uchun ma'lumot yo'q.")
            return

        # Prepare formatting data
        current_view_date = start_date + timedelta(days=day_idx-1)
        weekday_name = get_weekday_name(current_view_date)
        user_goal = db.get_user(user_id).get('goal', 'Sog\'lom Hayot')
        
        # Translate goal (Quick map)
        goal_map = {"weight_loss": "Vazn yo'qotish", "muscle_gain": "Mushak o'stirish", "health": "Sog'lom turmush"}
        user_goal = goal_map.get(user_goal, user_goal)

        # 1. Header
        txt = f"🍽 <b>✨ {day_idx}-KUN MENYU</b>\n"
        txt += f"🎯 <b>Maqsad:</b> {_esc(user_goal)} | 📅 {weekday_name}\n\n"
        
        # 2. Meal Content
        meal_data = day_data.get(meal_type)
        
        meal_labels = {
            'breakfast': '🍳 Nonushta',
            'lunch': '🥗 Tushlik',
            'dinner': '🍲 Kechki ovqat',
            'snack': '🍏 Tamaddi'
        }
        
        label = meal_labels.get(meal_type, meal_type.title())
        
        if isinstance(meal_data, dict):
            title = meal_data.get('title', 'Noma\'lum taom')
            kcal = meal_data.get('kcal', 0)
            
            txt += f"{label}: {_esc(title)}\n"
            if kcal: txt += f"🔥 {kcal} kkal\n\n"
            
            # Ingredients
            ings = meal_data.get('ingredients', [])
            if ings:
                # Escape each ingredient
                safe_ings = [_esc(i) for i in ings]
                txt += "<b>Tarkibi:</b> " + ", ".join(safe_ings) + "\n\n"
            
            # Steps
            steps = meal_data.get('preparation_steps', [])
            if steps:
                txt += "<b>Tayyorlanishi:</b>\n"
                for i, step in enumerate(steps, 1):
                    txt += f"{i}. {_esc(step)}\n"
                txt += "\n"
            
            # Meta
            time_m = meal_data.get('time_minutes')
            if time_m: txt += f"⌛ Tayyorlanish vaqti: {time_m} daqiqa\n"
            
        else:
            safe_val = _esc(meal_data) if isinstance(meal_data, str) else 'Ma\'lumot yo\'q'
            txt += f"{label}: {safe_val}\n"

        # 3. Dynamic Buttons
        markup = InlineKeyboardMarkup()
        
        # Row 1: "Iste'mol qildim"
        markup.row(InlineKeyboardButton("🍽 Iste'mol qildim (+kaloriya)", callback_data=f"eat_{day_idx}_{meal_type}"))
        
        # Row 2: Other Main Meals
        main_meals_row = []
        if meal_type == 'breakfast':
            main_meals_row.append(InlineKeyboardButton("🥗 Tushlik", callback_data=f"menu_view_{day_idx}_lunch"))
            main_meals_row.append(InlineKeyboardButton("🍲 Kechki", callback_data=f"menu_view_{day_idx}_dinner"))
        elif meal_type == 'lunch':
            main_meals_row.append(InlineKeyboardButton("🍳 Nonushta", callback_data=f"menu_view_{day_idx}_breakfast"))
            main_meals_row.append(InlineKeyboardButton("🍲 Kechki", callback_data=f"menu_view_{day_idx}_dinner"))
        elif meal_type == 'dinner':
            main_meals_row.append(InlineKeyboardButton("🍳 Nonushta", callback_data=f"menu_view_{day_idx}_breakfast"))
            main_meals_row.append(InlineKeyboardButton("🥗 Tushlik", callback_data=f"menu_view_{day_idx}_lunch"))
        else: # Snack
            main_meals_row.append(InlineKeyboardButton("🥗 Tushlik", callback_data=f"menu_view_{day_idx}_lunch"))
            main_meals_row.append(InlineKeyboardButton("🍲 Kechki", callback_data=f"menu_view_{day_idx}_dinner"))
        
        markup.row(*main_meals_row)
        
        # Row 3: Snack + Navigation
        snack_nav_row = []
        if meal_type != 'snack':
             snack_nav_row.append(InlineKeyboardButton("🍏 Tamaddi", callback_data=f"menu_view_{day_idx}_snack"))
        
        # Day Navigation
        if day_idx < total_days:
            snack_nav_row.append(InlineKeyboardButton("➡️ Ertangi menyu", callback_data=f"menu_view_{day_idx+1}_breakfast"))
        elif day_idx > 1:
             snack_nav_row.append(InlineKeyboardButton("⬅️ Kechagi menyu", callback_data=f"menu_view_{day_idx-1}_breakfast"))
        
        markup.row(*snack_nav_row)
        
        # Row 4: Tools
        markup.row(
            InlineKeyboardButton("🛒 Bozorlik", callback_data="menu_shopping"),
            InlineKeyboardButton("🔄 Almashtirish (VIP)", callback_data="menu_swap_vip")
        )
        
        bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup)

    except Exception as e:
        print(f"Show Menu Error: {e}")
        bot.send_message(user_id, "❌ Menyu ochishda xatolik.")

def handle_menu_callback(call, bot):
    """
    Handles menu navigation callbacks:
    - menu_view_{day}_{meal_type}
    - eat_{day}_{meal_type}
    """
    user_id = call.from_user.id
    data = call.data
    
    if data.startswith("menu_view_"):
        parts = data.split("_")
        # menu_view_1_lunch
        if len(parts) >= 4:
            day_idx = int(parts[2])
            meal_type = parts[3]
            
            link = db.get_user_menu_link(user_id)
            if link:
                # Delete previous message to keep chat clean (simulating app-like feel)
                try:
                    bot.delete_message(user_id, call.message.message_id)
                except: pass
                
                show_daily_menu(bot, user_id, link, day_idx, meal_type)
        return

    if data.startswith("eat_"):
        # eat_1_breakfast
        bot.answer_callback_query(call.id, "✅ Kaloriyalar qo'shildi! (Tez orada...)")
        # TODO: Implement actual tracking logic
        return

    if data == "menu_fridge":
         bot.answer_callback_query(call.id, "🥦 Muzlatgich retsepti tez orada!", show_alert=True)
         return
         
    if data == "menu_swap_vip":
         bot.answer_callback_query(call.id, "🔄 Taomni almashtirish (VIP) tez orada!", show_alert=True)
         return
         
    if data == "menu_regenerate":
        bot.answer_callback_query(call.id, "🔄 Yangi reja tuzish tez orada!", show_alert=True)
        return
