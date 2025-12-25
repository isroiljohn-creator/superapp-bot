from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import os
from core.config import ADMIN_IDS
from bot.languages import get_text

def language_selection_keyboard():
    """Keyboard for selecting bot language"""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )
    return markup

def phone_request_keyboard(lang="uz"):
    """Request phone number from user"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_text = "📱 Telefon raqamni yuborish" if lang == "uz" else "📱 Отправить номер телефона"
    markup.add(KeyboardButton(btn_text, request_contact=True))
    return markup

def gender_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    male_text = "Erkak 🧑🏻‍🦱" if lang == "uz" else "Мужчина 🧑🏻‍🦱"
    female_text = "Ayol 👩🏻" if lang == "uz" else "Женщина 👩🏻"
    markup.row(
        InlineKeyboardButton(male_text, callback_data="gender_male"),
        InlineKeyboardButton(female_text, callback_data="gender_female")
    )
    return markup

def goal_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    if lang == "ru":
        markup.add(InlineKeyboardButton("Похудение 🔻", callback_data="goal_weight_loss"))
        markup.add(InlineKeyboardButton("Набор массы 🔺", callback_data="goal_muscle_gain"))
        markup.add(InlineKeyboardButton("Поддержание веса ❤️", callback_data="goal_health"))
    else:
        markup.add(InlineKeyboardButton("Vazn tashlash 🔻", callback_data="goal_weight_loss"))
        markup.add(InlineKeyboardButton("Vazn olish 🔺", callback_data="goal_muscle_gain"))
        markup.add(InlineKeyboardButton("Vaznni ushlab turish ❤️", callback_data="goal_health"))
    return markup

def activity_level_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=1)
    if lang == "ru":
        markup.add(
            InlineKeyboardButton("Малоподвижный 🪑", callback_data="activity_sedentary"),
            InlineKeyboardButton("Легкая активность 🚶‍♂️", callback_data="activity_light"),
            InlineKeyboardButton("Умеренная активность 🏃‍♂️", callback_data="activity_moderate"),
            InlineKeyboardButton("Высокая активность 🏋️‍♂️", callback_data="activity_active"),
            InlineKeyboardButton("Атлет 🔥", callback_data="activity_athlete")
        )
    else:
        markup.add(
            InlineKeyboardButton("Kam harakat 🪑", callback_data="activity_sedentary"),
            InlineKeyboardButton("Yengil faol 🚶‍♂️", callback_data="activity_light"),
            InlineKeyboardButton("O'rtacha faol 🏃‍♂️", callback_data="activity_moderate"),
            InlineKeyboardButton("Juda faol 🏋️‍♂️", callback_data="activity_active"),
            InlineKeyboardButton("Atlet 🔥", callback_data="activity_athlete")
        )
    return markup

def allergy_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    no_text = "Yo‘q ❌" if lang == "uz" else "Нет ❌"
    yes_text = "Ha ✅" if lang == "uz" else "Да ✅"
    markup.row(
        InlineKeyboardButton(no_text, callback_data="allergy_no"),
        InlineKeyboardButton(yes_text, callback_data="allergy_yes")
    )
    return markup

def main_menu_keyboard(is_admin=False, user_id=None, lang=None):
    """
    Generate Main Menu Reply Keyboard.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Calculate admin status securely
    real_admin = False
    if user_id:
        real_admin = int(user_id) in ADMIN_IDS
        if lang is None:
            from core.db import db
            lang = db.get_user_language(user_id)
    
    if lang is None: lang = "uz"

    # Row 1: AI Murabbiy | Ilovani ochish
    coach_text = "🤖 AI murabbiy" if lang == "uz" else "🤖 AI тренер"
    app_text = "📱 Ilovani ochish" if lang == "uz" else "📱 Открыть приложение"
    
    mini_app_url = os.getenv("MINI_APP_URL", "https://obsid.uz")
    
    markup.add(
        KeyboardButton(coach_text),
        KeyboardButton(app_text, web_app=WebAppInfo(url=mini_app_url))
    )
    
    # Row 2: Kaloriya tahlili | YASHA Plus
    scan_text = "🍽 Kaloriya tahlili" if lang == "uz" else "🍽 Анализ калорий"
    plus_text = "💚 YASHA Plus"
    markup.add(KeyboardButton(scan_text), KeyboardButton(plus_text))
    
    # Row 3: Profil | Yordam
    profile_text = "👤 Profil" if lang == "uz" else "👤 Профиль"
    help_text = "📩 Yordam" if lang == "uz" else "📩 Помощь"
    markup.add(KeyboardButton(profile_text), KeyboardButton(help_text))
    
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
    markup = InlineKeyboardMarkup(row_width=1)
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
    # Challenges inside Yasha Plus
    markup.row(InlineKeyboardButton("🔥 Chellenjlar", callback_data="premium_challenges"))
    return markup

def gamification_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Mashq qildim ✅", callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton("Suv ichdim 💧", callback_data="daily_water_done"))
    return markup

def ai_coach_submenu_keyboard():
    """Reply Submenu for '🤖 AI murabbiy' (Legacy - kept for fallback)"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🏋️ Mashq qilaman"), KeyboardButton("🥗 Nima yeyman?"))
    markup.add(KeyboardButton("🔥 AI retsept tuzsin"), KeyboardButton("🛒 Nima xarid qilay?"))
    markup.add(KeyboardButton("❓ Murabbiyga savolim bor"), KeyboardButton("⬅️ Orqaga"))
    return markup

def ai_coach_inline_keyboard():
    """Inline Submenu for '🤖 AI murabbiy'"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏋️ Mashq rejasi", callback_data="ai_sub_workout"),
        InlineKeyboardButton("🥗 Ovqat menyusi", callback_data="ai_sub_meal")
    )
    markup.add(
        InlineKeyboardButton("🔥 AI retsept", callback_data="ai_sub_recipe"),
        InlineKeyboardButton("🛒 Xaridlar ro'yxati", callback_data="ai_sub_shopping")
    )
    markup.add(
        InlineKeyboardButton("❓ Murabbiyga savol", callback_data="ai_sub_qa"),
        InlineKeyboardButton("⬅️ Orqaga", callback_data="ai_sub_close")
    )
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

def admin_analytics_keyboard():
    """Inline keyboard for navigating analytics sections."""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📈 O'sish (Growth)", callback_data="admin_stats_growth"),
        InlineKeyboardButton("🌪 Voronka (Funnel)", callback_data="admin_stats_funnel")
    )
    markup.add(
        InlineKeyboardButton("📉 Retention", callback_data="admin_stats_retention"),
        InlineKeyboardButton("💎 Premium", callback_data="admin_stats_premium")
    )
    markup.add(
        InlineKeyboardButton("🔄 Yangilash", callback_data="admin_stats_refresh")
    )
    return markup

def admin_developer_keyboard():

    """
    Main menu for Developers/Admins. Consolidates all /commands into buttons.
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Analitika (Pro)", callback_data="dev_stats_menu"),
        InlineKeyboardButton("🗑 Foydalanuvchini o'chirish", callback_data="dev_delete_user_start")
    )
    markup.add(
        InlineKeyboardButton("🧪 AI ni tekshirish", callback_data="dev_test_ai_start"),
        InlineKeyboardButton("🚩 Feature Flags", callback_data="dev_flags_menu")
    )
    markup.add(
        InlineKeyboardButton("📢 Xabar yuborish (Broadcast)", callback_data="dev_broadcast_menu"),
        InlineKeyboardButton("📦 Backup", callback_data="dev_backup_menu")
    )
    markup.add(
        InlineKeyboardButton("✍️ Matnlar (Content)", callback_data="dev_content_menu")
    )

    return markup
