from telebot import types
from core.db import db
from core.utils import generate_referral_code, get_referrer_id_from_code
from bot.keyboards import (
    phone_request_keyboard, gender_keyboard, goal_keyboard, 
    allergy_keyboard, main_menu_keyboard
)

# Temporary storage for onboarding data
onboarding_data = {}

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
    
    # Handle referral code
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        code = args[1]
        referrer_id = get_referrer_id_from_code(code)
        
        # Prevent self-referral
        if referrer_id == user_id:
            referrer_id = None
    
    # Initialize onboarding data
    onboarding_data[user_id] = {'referrer_id': referrer_id}
    
    # Request phone number (CRITICAL FIRST STEP)
    bot.send_message(
        user_id,
        "🎉 Assalomu alaykum! YASHA botiga xush kelibsiz.\n\n"
        "Davom etish uchun telefon raqamingizni yuboring 👇",
        reply_markup=phone_request_keyboard()
    )

def process_phone(message, bot):
    """Step 1: Process phone number from contact"""
    user_id = message.from_user.id
    
    if not message.contact:
        # User sent text instead of contact
        bot.send_message(
            user_id,
            "❌ Iltimos, telefon raqamingizni kontakt sifatida yuboring 👇\n\n"
            "Pastdagi tugmani bosing:",
            reply_markup=phone_request_keyboard()
        )
        return
    
    # Save phone number
    phone = message.contact.phone_number
    onboarding_data[user_id]['phone'] = phone
    
    # Proceed to name
    msg = bot.send_message(
        user_id, 
        f"✅ Rahmat! Telefon raqamingiz saqlandi.\n\n"
        f"Endi ismingizni kiriting:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_name, bot)

def process_name(message, bot):
    """Step 2: Process name"""
    user_id = message.from_user.id
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    name = message.text.strip()
    onboarding_data[user_id]['name'] = name
    
    msg = bot.send_message(user_id, f"Rahmat, {name}! Yoshingiz nechida? (faqat raqam)")
    bot.register_next_step_handler(msg, process_age, bot)

def process_age(message, bot):
    """Step 3: Process age"""
    user_id = message.from_user.id
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    if not message.text.isdigit():
        msg = bot.send_message(user_id, "Iltimos, yoshingizni raqamda kiriting:")
        bot.register_next_step_handler(msg, process_age, bot)
        return
    
    age = int(message.text)
    if age < 10 or age > 120:
        msg = bot.send_message(user_id, "Yoshingizni to'g'ri kiriting (10-120 oralig'ida):")
        bot.register_next_step_handler(msg, process_age, bot)
        return
    
    onboarding_data[user_id]['age'] = age
    bot.send_message(user_id, "Jinsingizni tanlang:", reply_markup=gender_keyboard())

def process_gender(message, bot):
    """Step 4: Process gender (inline callback)"""
    user_id = message.from_user.id
    gender = message.data
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    onboarding_data[user_id]['gender'] = gender
    bot.answer_callback_query(message.id)
    
    msg = bot.send_message(user_id, "Bo'yingizni kiriting (sm):")
    bot.register_next_step_handler(msg, process_height, bot)

def process_height(message, bot):
    """Step 5: Process height"""
    user_id = message.from_user.id
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    if not message.text.isdigit():
        msg = bot.send_message(user_id, "Iltimos, bo'yingizni raqamda kiriting (sm):")
        bot.register_next_step_handler(msg, process_height, bot)
        return
    
    height = int(message.text)
    if height < 50 or height > 250:
        msg = bot.send_message(user_id, "Bo'yingizni to'g'ri kiriting (50-250 sm):")
        bot.register_next_step_handler(msg, process_height, bot)
        return
    
    onboarding_data[user_id]['height'] = height
    
    msg = bot.send_message(user_id, "Vazningizni kiriting (kg):")
    bot.register_next_step_handler(msg, process_weight, bot)

def process_weight(message, bot):
    """Step 6: Process weight"""
    user_id = message.from_user.id
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    try:
        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
    except ValueError:
        msg = bot.send_message(user_id, "Vazningizni to'g'ri kiriting (20-300 kg):")
        bot.register_next_step_handler(msg, process_weight, bot)
        return
    
    onboarding_data[user_id]['weight'] = weight
    bot.send_message(user_id, "Maqsadingizni tanlang:", reply_markup=goal_keyboard())

def process_goal(message, bot):
    """Step 7: Process goal (inline callback)"""
    user_id = message.from_user.id
    goal = message.data
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    onboarding_data[user_id]['goal'] = goal
    bot.answer_callback_query(message.id)
    
    bot.send_message(user_id, "Allergiyangiz bormi?", reply_markup=allergy_keyboard())

def process_allergy(message, bot):
    """Step 8: Process allergy (inline callback) and finish onboarding"""
    user_id = message.from_user.id
    allergy = message.data
    
    # Block if user somehow got here without phone
    if user_id not in onboarding_data or 'phone' not in onboarding_data[user_id]:
        bot.send_message(
            user_id,
            "Davom etish uchun telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_keyboard()
        )
        return
    
    onboarding_data[user_id]['allergies'] = allergy
    bot.answer_callback_query(message.id)
    
    # Save to database
    data = onboarding_data[user_id]
    referrer_id = data.get('referrer_id')
    
    # Add user to database (phone is required!)
    db.add_user(
        telegram_id=user_id,
        username=message.from_user.username or f"user_{user_id}",
        phone=data['phone']
    )
    
    # Update profile
    db.update_user_profile(
        user_id=user_id,
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
        goal=data.get('goal'),
        allergies=data.get('allergies')
    )
    
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
    
    # Clean up onboarding data
    del onboarding_data[user_id]
    
    # Send welcome message with main menu
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
        """Handle phone number contact"""
        process_phone(message, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data in ['male', 'female'])
    def handle_gender(call):
        # Only process if user is in onboarding and has phone
        if call.from_user.id in onboarding_data and 'phone' in onboarding_data[call.from_user.id]:
            process_gender(call, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data in ['weight_loss', 'mass_gain', 'health'])
    def handle_goal(call):
        # Only process if user is in onboarding and has phone
        if call.from_user.id in onboarding_data and 'phone' in onboarding_data[call.from_user.id]:
            process_goal(call, bot)
    
    @bot.callback_query_handler(func=lambda call: call.data in ['yes_allergy', 'no_allergy'])
    def handle_allergy(call):
        # Only process if user is in onboarding and has phone
        if call.from_user.id in onboarding_data and 'phone' in onboarding_data[call.from_user.id]:
            process_allergy(call, bot)
