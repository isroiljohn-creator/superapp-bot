from telebot import types
from core.db import db
from core.utils import generate_referral_code, get_referrer_id_from_code
from bot.keyboards import (
    phone_request_keyboard, gender_keyboard, goal_keyboard, 
    allergy_keyboard, main_menu_keyboard
)
from bot.languages import get_text

# States
STATE_LANGUAGE = 0
STATE_PHONE = 8 # Added missing state
STATE_NAME = 1
STATE_AGE = 2
STATE_GENDER = 3
STATE_HEIGHT = 4
STATE_WEIGHT = 5
STATE_GOAL = 6
STATE_ALLERGY = 7

class OnboardingManager:
    def __init__(self):
        self.user_states = {}
        self.user_data = {}

    def get_state(self, user_id):
        return self.user_states.get(user_id)

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
    user_id = message.from_user.id
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
        f"✅ Rahmat! Telefon raqamingiz saqlandi.\n\n"
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
    lang = db.get_language(user_id)
    try:
        height = int(message.text)
    except ValueError:
        bot.send_message(user_id, get_text("error_number", lang))
        return

    manager.update_data(user_id, 'height', height)
    manager.set_state(user_id, STATE_WEIGHT)
    bot.send_message(user_id, get_text("enter_weight", lang))

def process_weight(message, bot):
    user_id = message.from_user.id
    lang = db.get_language(user_id)
    try:
        weight = float(message.text)
    except ValueError:
        bot.send_message(user_id, get_text("error_number", lang))
        return

    manager.update_data(user_id, 'weight', weight)
    manager.set_state(user_id, STATE_GOAL)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(get_text("goal_weight_loss", lang), get_text("goal_mass_gain", lang))
    markup.add(get_text("goal_health", lang))
    
    bot.send_message(user_id, get_text("enter_goal", lang), reply_markup=markup)

def process_goal(message, bot):
    user_id = message.from_user.id
    goal = message.text
    lang = db.get_language(user_id)
    
    manager.update_data(user_id, 'goal', goal)
    manager.set_state(user_id, STATE_ALLERGY)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(get_text("no", lang), get_text("yes", lang))
    
    bot.send_message(user_id, get_text("allergy_question", lang), reply_markup=markup)

def process_allergy(message, bot):
    user_id = message.from_user.id
    text = message.text
    lang = db.get_language(user_id)
    
    if text == get_text("yes", lang):
        # Ask for details
        msg = bot.send_message(user_id, get_text("enter_allergy", lang), reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_allergy_details, bot)
    else:
        # No allergy, finish
        manager.update_data(user_id, 'allergies', "Yo'q")
        finish_onboarding(message, bot)

def process_allergy_details(message, bot):
    user_id = message.from_user.id
    allergies = message.text
    manager.update_data(user_id, 'allergies', allergies)
    finish_onboarding(message, bot)

def finish_onboarding(message, bot):
    user_id = message.from_user.id
    data = manager.get_data(user_id)
    lang = db.get_language(user_id)
    
    # Save to DB
    # Note: add_user was called in process_language, so we update here
    db.update_user_profile(
        user_id,
        full_name=data.get('first_name'),
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
        goal=data.get('goal'),
        allergies=data.get('allergies')
    )
    
    
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith('goal_'))
    def handle_goal_step(call):
        try:
            # Extract goal value (weight_loss/muscle_gain/health)
            goal_val = call.data.split('_', 1)[1] # Split only on first underscore
            
            bot.answer_callback_query(call.id)
            
            user_id = call.from_user.id
            manager.update_data(user_id, 'goal', goal_val)
            manager.set_state(user_id, STATE_ALLERGY)
            
            bot.send_message(user_id, "Allergiyangiz bormi?", reply_markup=allergy_keyboard())
            
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

