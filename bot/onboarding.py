from telebot import types
from core.db import db
from core.utils import generate_referral_code, get_referrer_id_from_code
from bot.keyboards import (
    phone_request_keyboard, gender_keyboard, goal_keyboard, 
    allergy_keyboard, main_menu_keyboard, activity_level_keyboard
)

# States
STATE_NONE = 0
STATE_PHONE = 1
STATE_NAME = 2
STATE_AGE = 3
STATE_GENDER = 4
STATE_HEIGHT = 5
STATE_WEIGHT = 6
STATE_ACTIVITY = 9 # New state
STATE_GOAL = 7
STATE_ALLERGY = 8
STATE_CALORIE_PHOTO = 10
STATE_CALORIE_TEXT = 11

class OnboardingManager:
    def __init__(self):
        self.user_states = {}
        self.user_data = {}

    def get_state(self, user_id):
        return self.user_states.get(user_id, STATE_NONE)

    def set_state(self, user_id, state):
        self.user_states[user_id] = state

    def update_data(self, user_id, key, value):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id][key] = value

    def get_data(self, user_id):
        return self.user_data.get(user_id, {})

    def track_message(self, user_id, message_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        if 'msg_ids' not in self.user_data[user_id]:
            self.user_data[user_id]['msg_ids'] = []
        self.user_data[user_id]['msg_ids'].append(message_id)

    def get_messages(self, user_id):
        return self.user_data.get(user_id, {}).get('msg_ids', [])

    def clear_user(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_data:
            del self.user_data[user_id]

manager = OnboardingManager()

from bot.languages import get_text

# ... (imports)

# ... (OnboardingManager class)

manager = OnboardingManager()

def start_onboarding(message, bot):
    """Step 0: Check if user exists, if not request Language FIRST"""
    user_id = message.from_user.id
    
    # Check if user already exists in database
    existing_user = db.get_user(user_id)
    if existing_user:
        lang = existing_user.get('language', 'uz')
        bot.send_message(
            user_id, 
            get_text("welcome", lang, name=message.from_user.first_name), 
            reply_markup=main_menu_keyboard(lang)
        )
        return
    
    # Handle start parameters
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        code = args[1]
        
        # Handle premium shortcut
        if code == 'premium':
            from bot.premium import handle_premium_menu
            handle_premium_menu(message, bot)
            return
            
        referrer_id = get_referrer_id_from_code(code)
        
        # Prevent self-referral
        if referrer_id == user_id:
            referrer_id = None
    
    # Initialize onboarding
    manager.clear_user(user_id)
    # manager.set_state(user_id, STATE_PHONE) # Don't set state yet, wait for lang
    manager.update_data(user_id, 'referrer_id', referrer_id)
    manager.update_data(user_id, 'msg_ids', []) # Init message tracking
    
    # Track user's start command
    manager.track_message(user_id, message.message_id)
    
    # Language Selection
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"))
    markup.add(types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"))
    markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    
    msg = bot.send_message(
        user_id,
        "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык / 🇬🇧 Select language",
        reply_markup=markup
    )
    manager.track_message(user_id, msg.message_id)

def handle_language_callback(call, bot):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    
    # Save language to manager
    manager.update_data(user_id, "language", lang)
    
    # Delete selection message (or answer it)
    bot.answer_callback_query(call.id)
    # We don't delete it here because track_message handles cleanup later, 
    # BUT for a smooth transition we might want to delete it or edit it.
    # Let's delete it to keep chat clean as per "Cleanup" task.
    # Actually, delete_tracked_messages is called at the END. 
    # So we can leave it or delete it. Let's delete it to be clean immediately.
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    
    # Ask for phone
    manager.set_state(user_id, STATE_PHONE)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_text = "📱 Telefon raqamni yuborish" # Default fallback
    if lang == "ru": btn_text = "📱 Отправить номер телефона"
    elif lang == "en": btn_text = "📱 Send Phone Number"
    
    markup.add(types.KeyboardButton(btn_text, request_contact=True))
    
    text_key = "enter_phone" 
    # Note: enter_phone key might not exist in languages.py yet, need to check/add it.
    # I'll assume I need to add it or use a hardcoded fallback if missing.
    # Let's use get_text with a default.
    msg_text = get_text("enter_phone", lang)
    if msg_text == "enter_phone": # Key missing
        if lang == "ru": msg_text = "Отправьте ваш номер телефона:"
        elif lang == "en": msg_text = "Please send your phone number:"
        else: msg_text = "Telefon raqamingizni yuboring:"
    
    msg = bot.send_message(
        user_id,
        msg_text,
        reply_markup=markup
    )
    manager.track_message(user_id, msg.message_id)

def process_phone(message, bot):
    user_id = message.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_PHONE:
        return

    phone = None
    if message.contact:
        phone = message.contact.phone_number
    elif message.text and message.text.replace('+', '').isdigit(): # Allow manual input if it looks like a phone number
        phone = message.text
    
    if not phone:
        bot.send_message(
            user_id,
            get_text("invalid_phone_format", lang),
            reply_markup=phone_request_keyboard(lang)
        )
        return
    
    manager.update_data(user_id, 'phone', phone)
    manager.set_state(user_id, STATE_NAME)
    
    # Track user message
    manager.track_message(user_id, message.message_id)
    
    msg = bot.send_message(
        user_id, 
        get_text("enter_name", lang),
        reply_markup=types.ReplyKeyboardRemove()
    )
    manager.track_message(user_id, msg.message_id)

def process_name(message, bot):
    user_id = message.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_NAME:
        return
    
    name = message.text.strip()
    if not name:
        bot.send_message(user_id, get_text("name_cannot_be_empty", lang))
        return

    manager.update_data(user_id, 'name', name)
    manager.set_state(user_id, STATE_AGE)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("enter_age", lang, name=name))
    manager.track_message(user_id, msg.message_id)

def process_age(message, bot):
    user_id = message.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_AGE:
        return
    
    if not message.text.isdigit():
        bot.send_message(user_id, get_text("enter_age_error", lang))
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        bot.send_message(user_id, get_text("enter_age_range_error", lang))
        return
    
    manager.update_data(user_id, 'age', age)
    manager.set_state(user_id, STATE_GENDER)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("enter_gender", lang), reply_markup=gender_keyboard(lang))
    manager.track_message(user_id, msg.message_id)

def process_gender(call, bot):
    user_id = call.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_GENDER:
        try:
            bot.answer_callback_query(call.id, get_text("old_button", lang))
        except:
            pass
        return
    
    gender = call.data
    manager.update_data(user_id, 'gender', gender)
    manager.set_state(user_id, STATE_HEIGHT)
    
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        pass
        
    msg = bot.send_message(user_id, get_text("enter_height", lang))
    manager.track_message(user_id, msg.message_id)

def process_height(message, bot):
    user_id = message.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_HEIGHT:
        return
    
    if not message.text.isdigit():
        bot.send_message(user_id, get_text("enter_height_error", lang))
        return
    
    height = int(message.text)
    if height < 50 or height > 250:
        bot.send_message(user_id, get_text("enter_height_range_error", lang))
        return
    
    manager.update_data(user_id, 'height', height)
    manager.set_state(user_id, STATE_WEIGHT)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("enter_weight", lang))
    manager.track_message(user_id, msg.message_id)

def process_weight(message, bot):
    user_id = message.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_WEIGHT:
        return
    
    try:
        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, get_text("enter_weight_error", lang))
        return
    
    manager.update_data(user_id, 'weight', weight)
    manager.set_state(user_id, STATE_ACTIVITY)
    
    manager.track_message(user_id, message.message_id)
    msg = bot.send_message(user_id, get_text("choose_activity", lang), reply_markup=activity_level_keyboard(lang))
    manager.track_message(user_id, msg.message_id)

def process_activity(call, bot):
    user_id = call.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_ACTIVITY:
        try:
            bot.answer_callback_query(call.id, get_text("old_button", lang))
        except:
            pass
        return
    
    activity = call.data.replace("activity_", "")
    manager.update_data(user_id, 'activity_level', activity)
    manager.set_state(user_id, STATE_GOAL)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    msg = bot.send_message(user_id, get_text("choose_goal", lang), reply_markup=goal_keyboard(lang))
    manager.track_message(user_id, msg.message_id)

def process_goal(call, bot):
    user_id = call.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_GOAL:
        try:
            bot.answer_callback_query(call.id, get_text("old_button", lang))
        except:
            pass
        return
    
    goal = call.data
    manager.update_data(user_id, 'goal', goal)
    manager.set_state(user_id, STATE_ALLERGY)
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
        
    msg = bot.send_message(user_id, get_text("allergy_question", lang), reply_markup=allergy_keyboard(lang))
    manager.track_message(user_id, msg.message_id)

def process_allergy(call, bot):
    user_id = call.from_user.id
    user_data = manager.get_data(user_id)
    lang = user_data.get("language", "uz")
    
    if manager.get_state(user_id) != STATE_ALLERGY:
        try:
            bot.answer_callback_query(call.id, get_text("old_button", lang))
        except:
            pass
        return
    
    allergy_choice = call.data
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    
    if allergy_choice == "allergy_yes":
        # Ask for allergy details
        manager.set_state(user_id, STATE_NONE)  # Temporarily exit FSM for text input
        msg = bot.send_message(
            user_id,
            get_text("allergy_details_prompt", lang),
            reply_markup=types.ReplyKeyboardRemove()
        )
        manager.track_message(user_id, msg.message_id)
        bot.register_next_step_handler(msg, process_allergy_details, bot)
    else:
        # No allergy
        manager.update_data(user_id, 'allergies', None)
        finish_onboarding(user_id, message=call.message, bot=bot)

def process_allergy_details(message, bot):
    """Process allergy details text input"""
    user_id = message.from_user.id
    allergy_details = message.text.strip()
    
    manager.update_data(user_id, 'allergies', allergy_details)
    manager.track_message(user_id, message.message_id)
    
    # Finish Onboarding
    finish_onboarding(user_id, message=message, bot=bot)

def finish_onboarding(user_id, message, bot):
    data = manager.get_data(user_id)
    referrer_id = data.get('referrer_id')
    lang = data.get("language", "uz")
    
    # Add user to database
    db.add_user(
        telegram_id=user_id,
        username=message.chat.username or f"user_{user_id}",
        phone=data.get('phone'),
        language=lang
    )
    
    # Update profile
    db.update_user_profile(
        user_id=user_id,
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
        activity_level=data.get('activity_level'),
        goal=data.get('goal'),
        allergies=data.get('allergies')
    )
    
    # Activate 5-day Trial
    try:
        from datetime import datetime, timedelta
        trial_days = 5
        now = datetime.now()
        trial_end = now + timedelta(days=trial_days)
        
        db.set_premium(user_id, trial_days) # Reusing set_premium to set date
        
        # Update trial specific flags
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET trial_start = ?, trial_used = 1 WHERE telegram_id = ?", (now.isoformat(), user_id))
        conn.commit()
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error activating trial: {e}")
    
    # Handle referral rewards
    if referrer_id:
        db.add_points(referrer_id, 1)
        try:
            bot.send_message(
                referrer_id,
                f"🎉 Yangi do'st ro'yxatdan o'tdi! +1 ball olasiz.\n"
                f"Jami ballar: {db.get_user(referrer_id)['points']}"
            )
        except:
            pass
    
    # Delete Onboarding Messages
    delete_tracked_messages(user_id, bot)
    manager.clear_user(user_id) # Now clear
    
    # Send welcome message
    welcome_text = get_text("onboarding_complete", lang) + "\n\n" + get_text("premium_desc", lang)
    
    bot.send_message(
        user_id,
        welcome_text,
        reply_markup=main_menu_keyboard(lang),
        parse_mode="Markdown"
    )

def register_handlers(bot):
    """Register all onboarding-related handlers"""
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        start_onboarding(message, bot)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
    def handle_language_selection(call):
        handle_language_callback(call, bot)
    
    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        process_phone(message, bot)
        
    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_NAME)
    def handle_name_step(message):
        process_name(message, bot)

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_AGE)
    def handle_age_step(message):
        process_age(message, bot)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('gender_'))
    def handle_gender_step(call):
        try:
            # Extract actual gender value (male/female) from gender_male/gender_female
            gender_val = call.data.split('_')[1]
            
            # Answer callback immediately to stop loading animation
            bot.answer_callback_query(call.id)
            
            # Update state and data
            user_id = call.from_user.id
            manager.update_data(user_id, 'gender', gender_val)
            manager.set_state(user_id, STATE_HEIGHT)
            
            # Send next step message
            msg = bot.send_message(user_id, "Bo'yingizni kiriting (sm):")
            manager.track_message(user_id, msg.message_id)
            
            # Explicitly register next step just in case FSM generic handler misses it
            # (Though generic handler should catch it if state is set correctly)
            # bot.register_next_step_handler(msg, process_height, bot)
            
        except Exception as e:
            print(f"ERROR in handle_gender_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi. Qaytadan urining.")
            except:
                pass

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_HEIGHT)
    def handle_height_step(message):
        process_height(message, bot)

    @bot.message_handler(func=lambda m: manager.get_state(m.from_user.id) == STATE_WEIGHT)
    def handle_weight_step(message):
        process_weight(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('activity_'))
    def handle_activity_step(call):
        try:
            bot.answer_callback_query(call.id)
            process_activity(call, bot)
        except Exception as e:
            print(f"ERROR in handle_activity_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('goal_'))
    def handle_goal_step(call):
        try:
            # Extract goal value (weight_loss/muscle_gain/health)
            goal_val = call.data.split('_', 1)[1] # Split only on first underscore
            
            bot.answer_callback_query(call.id)
            
            user_id = call.from_user.id
            manager.update_data(user_id, 'goal', goal_val)
            manager.set_state(user_id, STATE_ALLERGY)
            
            msg = bot.send_message(user_id, "Qandaydir hastalik yoki biror mahsulotga allergiyangiz bormi?", reply_markup=allergy_keyboard())
            manager.track_message(user_id, msg.message_id)
            
        except Exception as e:
            print(f"ERROR in handle_goal_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('allergy_'))
    def handle_allergy_step(call):
        try:
            bot.answer_callback_query(call.id)
            # Call the actual process_allergy function that handles the logic
            process_allergy(call, bot)
        except Exception as e:
            print(f"ERROR in handle_allergy_step: {e}")
            try:
                bot.answer_callback_query(call.id, "Xatolik yuz berdi.")
            except:
                pass



def delete_tracked_messages(user_id, bot):
    """Deletes all tracked messages"""
    msg_ids = manager.get_messages(user_id)
    if not msg_ids:
        return
        
    for msg_id in msg_ids:
        try:
            bot.delete_message(user_id, msg_id)
        except Exception as e:
            # Message might be too old or already deleted
            # print(f"DEBUG: Failed to delete message {msg_id}: {e}")
            pass
