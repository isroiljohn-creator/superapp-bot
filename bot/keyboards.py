from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from bot.languages import get_text

def phone_request_keyboard(lang="uz"):
    """Request phone number from user"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton(get_text("btn_phone_request", lang), request_contact=True))
    return markup

def gender_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(get_text("male", lang), callback_data="gender_male"),
        InlineKeyboardButton(get_text("female", lang), callback_data="gender_female")
    )
    return markup

def goal_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(get_text("goal_weight_loss", lang), callback_data="goal_weight_loss"))
    markup.add(InlineKeyboardButton(get_text("goal_mass_gain", lang), callback_data="goal_muscle_gain"))
    markup.add(InlineKeyboardButton(get_text("goal_health", lang), callback_data="goal_health"))
    return markup

def activity_level_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(get_text("activity_sedentary", lang), callback_data="activity_sedentary"),
        InlineKeyboardButton(get_text("activity_light", lang), callback_data="activity_light"),
        InlineKeyboardButton(get_text("activity_moderate", lang), callback_data="activity_moderate"),
        InlineKeyboardButton(get_text("activity_active", lang), callback_data="activity_active"),
        InlineKeyboardButton(get_text("activity_athlete", lang), callback_data="activity_athlete")
    )
    return markup

def allergy_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(get_text("no", lang) + " ❌", callback_data="allergy_no"),
        InlineKeyboardButton(get_text("yes", lang) + " ✅", callback_data="allergy_yes")
    )
    return markup

def main_menu_keyboard(lang="uz"):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add(KeyboardButton(get_text("btn_calorie", lang)), KeyboardButton(get_text("btn_habits", lang)))
    markup.add(KeyboardButton(get_text("btn_trainer", lang)), KeyboardButton(get_text("btn_challenges", lang)))
    markup.add(KeyboardButton(get_text("btn_premium", lang)), KeyboardButton(get_text("btn_profile", lang)))
    markup.add(KeyboardButton(get_text("btn_referral", lang)), KeyboardButton(get_text("btn_feedback", lang)))
    
    return markup

def plan_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(get_text("btn_ai_workout", lang), callback_data="plan_ai_workout"),
        InlineKeyboardButton(get_text("btn_ai_meal", lang), callback_data="plan_ai_meal"),
        InlineKeyboardButton(get_text("btn_calorie_premium", lang), callback_data="plan_calorie_scan")
    )
    return markup

def habits_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(get_text("btn_water", lang), callback_data="habit_water"),
        InlineKeyboardButton(get_text("btn_sleep", lang), callback_data="habit_sleep"),
        InlineKeyboardButton(get_text("btn_mood", lang), callback_data="habit_mood"),
        InlineKeyboardButton(get_text("btn_steps", lang), callback_data="habit_steps"),
        InlineKeyboardButton(get_text("btn_habit_stats", lang), callback_data="habit_stats")
    )
    return markup

def ai_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(get_text("btn_ai_qa", lang), callback_data="ai_qa"),
        InlineKeyboardButton(get_text("btn_ai_meal", lang), callback_data="ai_meal"),
        InlineKeyboardButton(get_text("btn_ai_workout", lang), callback_data="ai_workout"),
        InlineKeyboardButton(get_text("btn_ai_recipe", lang), callback_data="ai_recipe"),
        InlineKeyboardButton(get_text("btn_ai_shopping", lang), callback_data="ai_shopping")
    )
    return markup

def points_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(get_text("btn_points", lang), callback_data="points_balance"),
        InlineKeyboardButton(get_text("btn_rewards", lang), callback_data="points_rewards"),
        InlineKeyboardButton(get_text("btn_rules", lang), callback_data="points_rules"),
        InlineKeyboardButton(get_text("btn_back_premium", lang), callback_data="back_premium")
    )
    return markup

def challenges_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(get_text("btn_weekly_challenge", lang), callback_data="challenge_weekly"),
        InlineKeyboardButton(get_text("btn_monthly_challenge", lang), callback_data="challenge_monthly"),
        InlineKeyboardButton(get_text("btn_friends_challenge", lang), callback_data="challenge_friends"),
        InlineKeyboardButton(get_text("btn_leaderboard", lang), callback_data="challenge_leaderboard")
    )
    return markup

def profile_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(get_text("btn_edit_profile", lang), callback_data="profile_edit"),
        InlineKeyboardButton(get_text("btn_health_stats", lang), callback_data="profile_stats"),
        InlineKeyboardButton(get_text("btn_change_goal", lang), callback_data="profile_change_goal")
    )
    return markup

def premium_inline_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    # Big button for Buy Premium
    markup.row(InlineKeyboardButton(get_text("btn_buy_premium", lang), callback_data="premium_buy"))
    # Two buttons in one row: Tariffs and Yasha Coin
    markup.row(
        InlineKeyboardButton(get_text("btn_tariffs", lang), callback_data="premium_info"),
        InlineKeyboardButton(get_text("btn_coins", lang), callback_data="premium_coins")
    )
    return markup

def gamification_keyboard(lang="uz"):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(get_text("btn_workout_done", lang), callback_data="daily_workout_done"))
    markup.add(InlineKeyboardButton(get_text("btn_water_done", lang), callback_data="daily_water_done"))
    return markup
