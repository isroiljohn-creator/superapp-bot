from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from core.config import ADMIN_IDS

def phone_request_keyboard():
    """Request phone number from user"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    return markup

def gender_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Erkak 🧑🏻‍🦱", callback_data="gender_male"),
        InlineKeyboardButton("Ayol 👩🏻", callback_data="gender_female")
    )
    return markup

def goal_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Vazn tashlash 🔻", callback_data="goal_weight_loss"))
    markup.add(InlineKeyboardButton("Vazn olish 🔺", callback_data="goal_muscle_gain"))
    markup.add(InlineKeyboardButton("Vaznni ushlab turish ❤️", callback_data="goal_health"))
    return markup

def activity_level_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Kam harakat 🪑", callback_data="activity_sedentary"),
        InlineKeyboardButton("Yengil faol 🚶‍♂️", callback_data="activity_light"),
        InlineKeyboardButton("O'rtacha faol 🏃‍♂️", callback_data="activity_moderate"),
        InlineKeyboardButton("Juda faol 🏋️‍♂️", callback_data="activity_active"),
        InlineKeyboardButton("Atlet 🔥", callback_data="activity_athlete")
    )
    return markup

def allergy_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Yo‘q ❌", callback_data="allergy_no"),
        InlineKeyboardButton("Ha ✅", callback_data="allergy_yes")
    )
    return markup

def main_menu_keyboard(is_admin=False, user_id=None):
    """
    Generate Main Menu Reply Keyboard.
    Args:
        is_admin (bool): Legacy override.
        user_id (int): If provided, checks against ADMIN_IDS.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Calculate admin status securely
    real_admin = False
    if user_id:
        real_admin = user_id in ADMIN_IDS
    elif is_admin: # This handles backward compatibility for is_admin=True
        real_admin = True
    
    # Calculate habit progress if user_id is present
    habit_text = "📅 Kunlik odatlar"
    if user_id:
        try:
            from core.db import db
            completed, total = db.get_daily_habit_progress(user_id)
            habit_text = f"📅 Kunlik odatlar ({completed}/{total})"
        except Exception as e:
            print(f"Error getting habit progress for menu: {e}")
        
    # Row 1: AI murabbiy (Full width or prominent)
    markup.add(KeyboardButton("🤖 AI murabbiy"))
    
    # Row 2: Kunlik odatlar | Kaloriya tahlili
    markup.add(KeyboardButton(habit_text), KeyboardButton("🍽 Kaloriya tahlili"))
    
    # Row 3: YASHA Plus | Profil
    markup.add(KeyboardButton("💚 YASHA Plus"), KeyboardButton("👤 Profil"))
    
    # Row 4: Chellenjlar | Yordam (Serving separate help menu now)
    markup.add(KeyboardButton("🔥 Chellenjlar"), KeyboardButton("📩 Yordam"))
    
    # Row 5: Admin Button (if admin)
    if real_admin:
        markup.add(KeyboardButton("👨‍💻 Dasturchi"), KeyboardButton("🗑 AI Bazani Tozalash"))
    
    return markup

def plan_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🤖 AI mashg‘ulot rejasi", callback_data="plan_ai_workout"),
        InlineKeyboardButton("🥦 AI ovqatlanish rejasi", callback_data="plan_ai_meal"),
        InlineKeyboardButton("🍽 Kaloriya tahlili (premium)", callback_data="plan_calorie_scan")
    )
    return markup

def habits_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💧 Suv trekeri", callback_data="habit_water"),
        InlineKeyboardButton("😴 Uyqu trekeri", callback_data="habit_sleep"),
        InlineKeyboardButton("🙂 Kayfiyat trekeri", callback_data="habit_mood"),
        InlineKeyboardButton("🚶🏻 Qadamlar", callback_data="habit_steps"),
        InlineKeyboardButton("📊 Odatlar statistikasi", callback_data="habit_stats")
    )
    return markup

def ai_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❓ AI savol-javob", callback_data="ai_qa"),
        InlineKeyboardButton("🍳 AI retsept", callback_data="ai_recipe"),
        InlineKeyboardButton("🥦 AI menyu", callback_data="ai_meal"),
        InlineKeyboardButton("🏋️ AI mashq rejasi", callback_data="ai_workout"),
        InlineKeyboardButton("🛒 AI shopping list", callback_data="ai_shopping")
    )
    return markup

def points_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Coinlarim", callback_data="points_balance"),
        InlineKeyboardButton("🎁 Mukofotlar", callback_data="points_rewards"),
        InlineKeyboardButton("📜 Qoidalar", callback_data="points_rules"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="back_premium")
    )
    return markup

def challenges_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📆 Haftalik challenge", callback_data="challenge_weekly"),
        InlineKeyboardButton("🗓 Oylik challenge", callback_data="challenge_monthly"),
        InlineKeyboardButton("👥 Do‘stlar challenge", callback_data="challenge_friends"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="challenge_leaderboard")
    )
    return markup

def profile_inline_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✏️ Anketani yangilash", callback_data="profile_edit"),
        InlineKeyboardButton("📊 Sog‘liq statistikasi", callback_data="profile_stats"),
        InlineKeyboardButton("🎯 Maqsadni o‘zgartirish", callback_data="profile_change_goal")
    )
    return markup

def premium_inline_keyboard():
    markup = InlineKeyboardMarkup()
    # Big button for Buy Premium
    markup.row(InlineKeyboardButton("💳 Tarifni almashtirish", callback_data="premium_buy"))
    # Two buttons in one row: Tariffs and Yasha Coin
    markup.row(
        InlineKeyboardButton("ℹ️ Tariflar", callback_data="premium_info"),
        InlineKeyboardButton("🟡 Yasha Coin", callback_data="premium_coins")
    )
    return markup

def gamification_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Mashq qildim ✅", callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton("Suv ichdim 💧", callback_data="daily_water_done"))
    return markup

def ai_coach_submenu_keyboard():
    """Submenu for '🤖 AI murabbiy'"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🏋️ Mashq qilaman"), KeyboardButton("🥗 Nima yeyman?"))
    markup.add(KeyboardButton("🔥 AI retsept tuzsin"), KeyboardButton("🛒 Nima xarid qilay?"))
    markup.add(KeyboardButton("❓ Murabbiyga savolim bor"), KeyboardButton("⬅️ Orqaga"))
    return markup

def challenges_submenu_keyboard():
    """Submenu for '🔥 Chellenjlar'"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🔥 Bugungi chellenj"), KeyboardButton("🏆 Reyting"))
    markup.add(KeyboardButton("👥 Do‘st chaqirish"), KeyboardButton("⬅️ Orqaga"))
    return markup

def help_submenu_keyboard():
    """Submenu for '📩 Yordam'"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🏋️ Mashqlar bo'yicha"), KeyboardButton("🥗 Menyu bo'yicha"))
    markup.add(KeyboardButton("💳 Obuna bo'yicha"), KeyboardButton("🤖 Bot ishlamayapti"))
    markup.add(KeyboardButton("⬅️ Orqaga"))
    return markup
