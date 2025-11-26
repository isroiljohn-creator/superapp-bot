from telebot import types
from core.db import db

def handle_profile(message, bot):
    user_id = message.from_user.id
    print(f"DEBUG: handle_profile called for user {user_id}")
    user = db.get_user(user_id)
    
    print(f"DEBUG: User data: {user}")
    
    if not user:
        print(f"DEBUG: User {user_id} not found in database")
        bot.send_message(user_id, "Siz hali ro'yxatdan o'tmagansiz. /start ni bosing.")
        return

    text = (
        f"👤 **Sizning Profilingiz**\n\n"
        f"🆔 ID: `{user.get('telegram_id')}`\n"
        f"👤 Ism: {user.get('full_name', 'Noma’lum')}\n"
        f"📱 Telefon: {user.get('phone', 'Yo’q')}\n"
        f"🎂 Yosh: {user.get('age', '-')}\n"
        f"📏 Bo'y: {user.get('height', '-')} sm\n"
        f"⚖️ Vazn: {user.get('weight', '-')} kg\n"
        f"🎯 Maqsad: {user.get('goal', '-')}\n"
        f"💰 Ballar: {user.get('points', 0)}\n"
        f"💎 Premium: {'✅ Aktiv' if user.get('is_premium') else '❌ Yo‘q'}\n"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ Vaznni o'zgartirish", callback_data="edit_weight"))
    markup.add(types.InlineKeyboardButton("✏️ Maqsadni o'zgartirish", callback_data="edit_goal"))
    
    print(f"DEBUG: Sending profile message to {user_id}")
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def register_handlers(bot):
    @bot.message_handler(commands=['profile'])
    def command_profile(message):
        handle_profile(message, bot)
        
    @bot.callback_query_handler(func=lambda call: call.data == "edit_weight")
    def edit_weight(call):
        msg = bot.send_message(call.from_user.id, "Yangi vazningizni kiriting (kg):")
        bot.register_next_step_handler(msg, process_new_weight, bot)

    @bot.callback_query_handler(func=lambda call: call.data == "edit_goal")
    def edit_goal(call):
        from bot.keyboards import goal_keyboard
        bot.send_message(call.from_user.id, "Yangi maqsadingizni tanlang:", reply_markup=goal_keyboard())
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('goal_'))
    def save_new_goal(call):
        # Extract goal from callback data (e.g., "goal_weight_loss" -> "goal_weight_loss")
        user_id = call.from_user.id
        goal = call.data  # Keep the full callback data
        db.update_user_profile(user_id, goal=goal)
        bot.answer_callback_query(call.id, "Maqsad yangilandi! ✅")
        bot.send_message(user_id, "✅ Maqsadingiz muvaffaqiyatli o'zgartirildi.")
        handle_profile(call.message, bot)

def process_new_weight(message, bot):
    user_id = message.from_user.id
    try:
        weight = float(message.text)
        if weight < 20 or weight > 300:
            raise ValueError
            
        db.update_user_profile(user_id, weight=weight)
        bot.send_message(user_id, f"✅ Vazningiz {weight} kg ga o'zgartirildi.")
        handle_profile(message, bot)
    except ValueError:
        bot.send_message(user_id, "❌ Noto'g'ri vazn. Qaytadan urinib ko'ring /profile")
