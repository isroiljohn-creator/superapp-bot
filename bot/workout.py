from core.db import db
from core.ai import ai_generate_workout, ai_generate_menu
from bot.languages import get_text
from telebot import types

def handle_workout_plan(message, bot):
    """Entry point for workout plans - show template menu"""
    handle_plan_menu(message, bot)

def handle_meal_plan(message, bot):
    """Entry point for meal plans - show template menu"""
    handle_plan_menu(message, bot)

def handle_plan_menu(message, bot):
    user_id = message.from_user.id
    lang = db.get_language(user_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text("btn_workout", lang), callback_data="get_workout"))
    markup.add(types.InlineKeyboardButton(get_text("btn_meal", lang), callback_data="get_meal"))
    
    bot.send_message(message.chat.id, get_text("choose_plan_type", lang), reply_markup=markup)

def generate_ai_workout(message, bot, user_id=None):
    """Generate AI workout plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
        
    lang = db.get_language(user_id)
    
    if not db.is_premium(user_id):
        # Free user -> Template
        # Note: get_template_workout needs to be updated to accept lang, or we just pass it and ignore if not supported yet
        # For now, let's assume get_template_workout handles it or we update it later.
        # Actually, let's check templates.py. It has send_template_plan.
        # But here we are calling get_template_workout which might not exist or be different.
        # Let's check imports.
        # Ah, in templates.py we have send_template_plan.
        # But here we imported get_template_workout.
        # Let's look at templates.py again. It DOES NOT have get_template_workout.
        # It has get_workout_templates (list) and send_template_plan (function).
        # So we should probably use show_workout_template_menu instead.
        
        from bot.templates import show_workout_template_menu
        show_workout_template_menu(message, bot)
        return

    # Premium -> AI
    msg = bot.send_message(user_id, get_text("generating_plan", lang))
    
    user_data = db.get_user(user_id)
    # Pass language to AI
    plan = ai_generate_workout(user_data, lang=lang) 
    
    bot.edit_message_text(plan, user_id, msg.message_id)

def generate_ai_meal(message, bot, user_id=None):
    """Generate AI meal plan (for premium users)"""
    if user_id is None:
        user_id = message.from_user.id
        
    lang = db.get_language(user_id)
    
    if not db.is_premium(user_id):
        # Free user -> Template
        from bot.templates import show_meal_template_menu
        show_meal_template_menu(message, bot)
        return

    # Premium -> AI
    msg = bot.send_message(user_id, get_text("generating_plan", lang))
    
    user_data = db.get_user(user_id)
    plan = ai_generate_menu(user_data, lang=lang)
    
    bot.edit_message_text(plan, user_id, msg.message_id)
