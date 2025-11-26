from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

def phone_request_keyboard():
    """Request phone number from user"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    return markup

def gender_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Erkak 👨", callback_data="gender_male"),
        InlineKeyboardButton("Ayol 👩", callback_data="gender_female")
    )
    return markup

def goal_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Ozish 🏃‍♂️", callback_data="goal_weight_loss"))
    markup.add(InlineKeyboardButton("Massa olish 💪", callback_data="goal_muscle_gain"))
    markup.add(InlineKeyboardButton("Sog‘liqni tiklash 🧘", callback_data="goal_health"))
    return markup

def allergy_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Yo‘q ❌", callback_data="allergy_no"),
        InlineKeyboardButton("Ha ✅", callback_data="allergy_yes")
    )
    return markup

def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add(
        KeyboardButton("Mening rejam 📅"),
        KeyboardButton("Menyu 🍏")
    )
    markup.add(
        KeyboardButton("Vazifalar ✅"),
        KeyboardButton("👤 Profil")
    )
    markup.add(
        KeyboardButton("💎 Premium"),
        KeyboardButton("📞 Qayta aloqa")
    )
    markup.add(KeyboardButton("🔗 Referal"))
    return markup

def gamification_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Mashq qildim ✅", callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton("Suv ichdim 💧", callback_data="daily_water_done"))
    return markup
