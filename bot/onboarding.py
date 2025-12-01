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

    def clear_user(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]
        if user_id in self.user_data:
            del self.user_data[user_id]

manager = OnboardingManager()

def start_onboarding(message, bot):
    """Step 0: Check if user exists, if not request phone number FIRST"""
    user_id = message.from_user.id
    
    # Check if user already exists in database
    existing_user = db.get_user(user_id)
    if existing_user:
        bot.send_message(
            user_id, 
            "Asosiy menyuga qaytdingiz, pastdagi tugmalar orqali keyingi qadamni tanlang👇🏻", 
            reply_markup=main_menu_keyboard()
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
    manager.set_state(user_id, STATE_PHONE)
    manager.update_data(user_id, 'referrer_id', referrer_id)
    
    bot.send_message(
        user_id,
        "🎉 Assalomu alaykum! YASHA botiga xush kelibsiz.\n\n"
        "Davom etish uchun telefon raqamingizni yuboring 👇",
        reply_markup=phone_request_keyboard()
    )

def process_phone(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_PHONE:
        return

    if not message.contact:
        bot.send_message(
            user_id,
            "❌ Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇\n\n"
            "Pastdagi tugmani bosing:",
            reply_markup=phone_request_keyboard()
        )
        return
    
    phone = message.contact.phone_number
    manager.update_data(user_id, 'phone', phone)
    manager.set_state(user_id, STATE_NAME)
    
    bot.send_message(
        user_id, 
        f"✅ Rahmat!\n\n"
        f"Endi ismingizni kiriting:",
        reply_markup=types.ReplyKeyboardRemove()
    )

def process_name(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_NAME:
        return
    
    name = message.text.strip()
    manager.update_data(user_id, 'name', name)
    manager.set_state(user_id, STATE_AGE)
    
    bot.send_message(user_id, f"Rahmat, {name}! Yoshingiz nechida? (faqat raqam)")

def process_age(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_AGE:
        return
    
    if not message.text.isdigit():
        bot.send_message(user_id, "Iltimos, yoshingizni raqamda kiriting:")
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        bot.send_message(user_id, "Yoshingizni to'g'ri kiriting (10-120 oralig'ida):")
        return
    
    manager.update_data(user_id, 'age', age)
    manager.set_state(user_id, STATE_GENDER)
    
    bot.send_message(user_id, "Jinsingizni tanlang:", reply_markup=gender_keyboard())

def process_gender(call, bot):
    user_id = call.from_user.id
    print(f"DEBUG: process_gender called for {user_id}, state: {manager.get_state(user_id)}")
    
    if manager.get_state(user_id) != STATE_GENDER:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
        except:
            pass
        return
    
    gender = call.data
    manager.update_data(user_id, 'gender', gender)
    manager.set_state(user_id, STATE_HEIGHT)
    print(f"DEBUG: State updated to STATE_HEIGHT for {user_id}")
    
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"DEBUG: Error answering callback: {e}")
        
    msg = bot.send_message(user_id, "Bo'yingizni kiriting (sm):")
    # Explicitly register next step handler as a backup for FSM
    # bot.register_next_step_handler(msg, process_height, bot) 
    # Actually, FSM should handle this via the generic handler in register_handlers
    # But let's make sure the generic handler is catching it.

def process_height(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_HEIGHT:
        return
    
    if not message.text.isdigit():
        bot.send_message(user_id, "Iltimos, bo'yingizni raqamda kiriting (sm):")
        return
    
    height = int(message.text)
    if height < 50 or height > 250:
        bot.send_message(user_id, "Bo'yingizni to'g'ri kiriting (50-250 sm):")
        return
    
    manager.update_data(user_id, 'height', height)
    manager.set_state(user_id, STATE_WEIGHT)
    
    bot.send_message(user_id, "Vazningizni kiriting (kg):")

def process_weight(message, bot):
    user_id = message.from_user.id
    
    if manager.get_state(user_id) != STATE_WEIGHT:
        return
    
    try:
        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
    except ValueError:
        bot.send_message(user_id, "Vazningizni to'g'ri kiriting (20-300 kg):")
        return
    
    manager.update_data(user_id, 'weight', weight)
    manager.set_state(user_id, STATE_ACTIVITY)
    
    bot.send_message(user_id, "Jismoniy faollik darajangizni tanlang:", reply_markup=activity_level_keyboard())

def process_activity(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_ACTIVITY:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
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
        
    bot.send_message(user_id, "Maqsadingizni tanlang:", reply_markup=goal_keyboard())

def process_goal(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_GOAL:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
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
        
    bot.send_message(user_id, "Hastaligingiz yoki allergiyangiz mavjudmi?", reply_markup=allergy_keyboard())

def process_allergy(call, bot):
    user_id = call.from_user.id
    
    if manager.get_state(user_id) != STATE_ALLERGY:
        try:
            bot.answer_callback_query(call.id, "Eski tugma.")
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
            "📝 Qanday hastalik yoki nima mahsulotlarga allergiyangiz bor?\n\n"
            "Masalan: yong'oq, sut, tuxum, gluten, dengiz mahsulotlari",
            reply_markup=types.ReplyKeyboardRemove()
        )
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
    
    # Finish Onboarding
    finish_onboarding(user_id, message=message, bot=bot)

def finish_onboarding(user_id, message, bot):
    data = manager.get_data(user_id)
    referrer_id = data.get('referrer_id')
    
    # Add user to database
    db.add_user(
        telegram_id=user_id,
        username=message.chat.username or f"user_{user_id}",
        phone=data.get('phone')
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
        conn.close()
        
        bot.send_message(
            user_id,
            f"🎁 **Sizga {trial_days} kunlik Premium sinov muddati yoqildi!**\n\n"
            "Barcha AI xizmatlar (Mashqlar, Ovqatlanish, Retseptlar) siz uchun ochiq. 🔥",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error activating trial: {e}")
    
    # Handle referral rewards
    if referrer_id:
        db.add_points(referrer_id, 5)
        try:
            bot.send_message(
                referrer_id,
                f"🎉 Yangi do'st ro'yxatdan o'tdi! +5 ball olasiz.\n"
                f"Jami ballar: {db.get_user(referrer_id)['points']}"
            )
        except:
            pass
    
    # Clear state
    manager.clear_user(user_id)
    
    # Send welcome message
    bot.send_message(
        user_id,
        f"✅ Ro'yxatdan o'tdingiz!\n\n"
        f"YASHA ga xush kelibsiz. Pastdagi tugmalar orqali botdan foydalanishingiz mumkin 👇",
        reply_markup=main_menu_keyboard()
    )

def register_handlers(bot):
    """Register all onboarding-related handlers"""
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        start_onboarding(message, bot)
    
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
            
            bot.send_message(user_id, "Qandaydir hastalik yoki biror mahsulotga allergiyangiz bormi?", reply_markup=allergy_keyboard())
            
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

