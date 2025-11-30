from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard, gender_keyboard, goal_keyboard, allergy_keyboard, activity_level_keyboard

import traceback

def handle_profile(message, bot):
    """Show user profile with edit options"""
    try:
        user_id = message.from_user.id
        print(f"DEBUG: handle_profile called for user {user_id}")
        
        # Test message to confirm handler reached
        # bot.send_message(user_id, "DEBUG: Profil yuklanmoqda...") 
        
        user = db.get_user(user_id)
        
        if not user:
            bot.send_message(user_id, "Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
            return

        # Format profile text
        text = (
            f"👤 Sizning Profilingiz\n\n"
            f"Ism: {user.get('full_name', 'Noma’lum')}\n"
            f"Yosh: {user.get('age', '-')} yosh\n"
            f"Jins: {user.get('gender', '-')}\n"
            f"Bo'y: {user.get('height', '-')} sm\n"
            f"Vazn: {user.get('weight', '-')} kg\n"
            f"Faollik: {user.get('activity_level', 'Belgilanmagan')}\n"
            f"Maqsad: {user.get('goal', '-')}\n"
            f"Allergiya: {user.get('allergies') or 'Yo‘q'}\n\n"
            f"⚙️ Qaysi qismni o'zgartirmoqchisiz?"
        )
        
        # Create inline keyboard for editing
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("Ism", callback_data="edit_full_name"),
            types.InlineKeyboardButton("Yosh", callback_data="edit_age"),
            types.InlineKeyboardButton("Jins", callback_data="edit_gender"),
            types.InlineKeyboardButton("Bo'y", callback_data="edit_height"),
            types.InlineKeyboardButton("Vazn", callback_data="edit_weight"),
            types.InlineKeyboardButton("Faollik", callback_data="edit_activity"),
            types.InlineKeyboardButton("Maqsad", callback_data="edit_goal"),
            types.InlineKeyboardButton("Allergiya", callback_data="edit_allergies"),
            types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_main")
        ]
        markup.add(*buttons)
        
        bot.send_message(user_id, text, reply_markup=markup)
        
    except Exception as e:
        error_msg = f"❌ Profil xatolik berdi:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            bot.send_message(message.from_user.id, error_msg[:4000]) # Telegram limit
        except:
            pass

def handle_edit_profile_menu(call, bot):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Ism", callback_data="edit_field_full_name"),
        types.InlineKeyboardButton("Yosh", callback_data="edit_field_age"),
        types.InlineKeyboardButton("Jins", callback_data="edit_field_gender"),
        types.InlineKeyboardButton("Bo'y", callback_data="edit_field_height"),
        types.InlineKeyboardButton("Vazn", callback_data="edit_field_weight"),
        types.InlineKeyboardButton("Faollik", callback_data="edit_field_activity"),
        types.InlineKeyboardButton("Maqsad", callback_data="edit_field_goal"),
        types.InlineKeyboardButton("Allergiya", callback_data="edit_field_allergies")
    )
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_profile"))
    
    bot.edit_message_text("Nimani o'zgartirmoqchisiz?", call.message.chat.id, call.message.message_id, reply_markup=markup)

def register_handlers(bot):
    """Register profile related handlers"""
    
    @bot.message_handler(commands=['profile'])
    def command_profile(message):
        handle_profile(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
    def back_to_main(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "Asosiy menyu", reply_markup=main_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data == "edit_profile_menu")
    def callback_edit_menu(call):
        handle_edit_profile_menu(call, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_profile")
    def callback_back_profile(call):
        # Re-render profile
        # user = db.get_user(call.from_user.id) # Not directly used here, handle_profile fetches it
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Trigger profile command logic manually or send new message
        # For now just delete and say "Profilga qaytdingiz"
        bot.answer_callback_query(call.id, "Profilga qaytdingiz")
        # Re-call handle_profile to show the main profile view
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "refresh_profile")
    def refresh_profile_callback(call):
        bot.answer_callback_query(call.id, "Ma'lumotlar yangilanmoqda...")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_field_"))
    def handle_edit_callback(call):
        field = call.data.replace("edit_field_", "")
        user_id = call.from_user.id
        
        bot.answer_callback_query(call.id)
        
        # Define prompts for each field
        prompts = {
            "full_name": "Yangi ismingizni kiriting:",
            "age": "Yangi yoshingizni kiriting (raqamda):",
            "gender": "Jinsingizni tanlang:",
            "height": "Yangi bo'yingizni kiriting (sm):",
            "weight": "Yangi vazningizni kiriting (kg):",
            "goal": "Yangi maqsadingizni tanlang:",
            "allergies": "Allergiyangiz bormi? (Ha/Yo'q yoki mahsulot nomlari):"
        }
        
        prompt = prompts.get(field, "Yangi qiymatni kiriting:")
        
        # Handle fields that need keyboards
        if field == "gender":
            bot.send_message(user_id, prompt, reply_markup=gender_keyboard())
        elif field == "goal":
            bot.send_message(user_id, prompt, reply_markup=goal_keyboard())
        elif field == "activity":
            bot.send_message(user_id, "Yangi faollik darajasini tanlang:", reply_markup=activity_level_keyboard())
        elif field == "allergies":
             # For allergies, we can use text input or the simple Yes/No keyboard.
             # Given the requirement "Yangi ... kiriting", text is more flexible for editing details.
             # But let's offer the keyboard first for simplicity, or just text if they want to list details.
             # Let's stick to text for editing to allow detailed input easily.
             msg = bot.send_message(user_id, "Yangi allergiya ma'lumotlarini yozing (yoki 'Yo'q' deb yozing):")
             bot.register_next_step_handler(msg, process_edit_input, bot, field)
             return
        else:
            msg = bot.send_message(user_id, prompt)
            bot.register_next_step_handler(msg, process_edit_input, bot, field)

    # Handlers for keyboard-based edits (Gender, Goal)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
    def process_gender_edit(call):
        user_id = call.from_user.id
        new_gender = call.data.split("_")[1] # male/female
        # Map to display text if needed, or store as is. DB stores 'male'/'female' usually or localized.
        # Let's verify what DB expects. onboarding.py uses 'male'/'female'.
        # Let's map to Uzbek for display consistency if DB stores raw.
        # Actually onboarding stores raw 'male'/'female'.
        
        db.update_user_profile(user_id, gender=new_gender)
        bot.answer_callback_query(call.id, "Jins yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("goal_"))
    def process_goal_edit(call):
        user_id = call.from_user.id
        new_goal = call.data # e.g. goal_weight_loss
        # We might want to strip 'goal_' prefix or store full string.
        # onboarding stores 'weight_loss'.
        # Let's strip 'goal_' to be consistent with onboarding.
        if new_goal.startswith("goal_"):
             new_goal = new_goal.replace("goal_", "")
             
        db.update_user_profile(user_id, goal=new_goal)
        bot.answer_callback_query(call.id, "Maqsad yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("activity_"))
    def process_activity_edit(call):
        user_id = call.from_user.id
        new_activity = call.data.replace("activity_", "")
        
        db.update_user_profile(user_id, activity_level=new_activity)
        bot.answer_callback_query(call.id, "Faollik darajasi yangilandi ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_profile(call.message, bot)

def process_edit_input(message, bot, field):
    """Process text input for profile editing"""
    user_id = message.from_user.id
    value = message.text
    
    try:
        # Validation and conversion
        if field == "age":
            if not value.isdigit() or not (10 <= int(value) <= 100):
                bot.send_message(user_id, "❌ Iltimos, to'g'ri yosh kiriting (10-100).")
                return
            value = int(value)
            
        elif field == "height":
            if not value.isdigit() or not (100 <= int(value) <= 250):
                bot.send_message(user_id, "❌ Iltimos, to'g'ri bo'y kiriting (100-250 sm).")
                return
            value = int(value)
            
        elif field == "weight":
            try:
                val = float(value)
                if not (30 <= val <= 300):
                    raise ValueError
                value = val
            except ValueError:
                bot.send_message(user_id, "❌ Iltimos, to'g'ri vazn kiriting (30-300 kg).")
                return
        
        # Update DB
        kwargs = {field: value}
        db.update_user_profile(user_id, **kwargs)
        
        bot.send_message(user_id, f"{field.capitalize()} yangilandi ✅")
        handle_profile(message, bot)
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        bot.send_message(user_id, "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")

