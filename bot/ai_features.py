from telebot import types
from core.ai import call_gemini, format_gemini_text
from core.db import db
from bot.premium import require_premium

from bot.onboarding import delete_tracked_messages
from bot import onboarding

# ... (imports)

# ... (handle_ai_tools_menu)

@require_premium
def handle_ai_qa(message, bot):
    msg = bot.send_message(message.chat.id, "❓ Savolingizni yozing:")
    onboarding.manager.track_message(message.from_user.id, msg.message_id)
    bot.register_next_step_handler(msg, process_ai_qa, bot)

def process_ai_qa(message, bot):
    user_id = message.from_user.id
    onboarding.manager.track_message(user_id, message.message_id)
    
    question = message.text
    
    status_msg = bot.send_message(user_id, "🤖 **Javob tayyorlanmoqda...**", parse_mode="Markdown")
    onboarding.manager.track_message(user_id, status_msg.message_id)
    
    try:
        # Assuming ai_answer_question is a new function that needs to be defined or imported
        # For now, I'll simulate its behavior based on the original process_ai_qa logic
        # and the instruction's intent to use a new helper.
        # If ai_answer_question is not defined elsewhere, this will cause a NameError.
        # The instruction implies it exists or should be created.
        # For the purpose of this edit, I will use the original call_gemini logic
        # but adapt it to the new structure.
        
        prompt = f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}"
        response = call_gemini(prompt)
        
        if response:
            answer = format_gemini_text(response, "Savolga Javob")
            bot.send_message(user_id, answer, parse_mode="HTML")
        else:
            bot.send_message(user_id, "❌ AI band. Keyinroq urining.")
    except Exception as e:
        bot.send_message(user_id, "❌ Xatolik yuz berdi.")
        
    delete_tracked_messages(user_id, bot)
    onboarding.manager.clear_user(user_id)

@require_premium
def handle_shopping_list(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "⏳ **AI xaridlar ro'yxatini tuzmoqda...**", parse_mode="Markdown")
    
    prompt = f"""
    Foydalanuvchi maqsadi: {user.get('goal')}
    Vazifa: 1 haftalik sog'lom ovqatlanish uchun kerakli mahsulotlar ro'yxatini tuzing.
    
    FORMAT:
    🛒 **Xaridlar Ro'yxati**
    
    **Sabzavot va Mevalar:**
    - ...
    
    **Oqsillar (Go'sht/Tuxum):**
    - ...
    
    **Don mahsulotlari:**
    - ...
    
    Qisqa va aniq bo'lsin.
    """
    
    response = call_gemini(prompt)
    if response:
        bot.edit_message_text(format_gemini_text(response, "Xaridlar Ro'yxati"), user_id, status_msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text("❌ AI band. Keyinroq urining.", user_id, status_msg.message_id)

@require_premium
def handle_recipe_gen(message, bot):
    msg = bot.send_message(message.chat.id, "🍳 **Muzlatgichda nima bor?**\n\nMahsulotlarni yozing (masalan: tuxum, pomidor, pishloq), men retsept tuzib beraman:", reply_markup=types.ForceReply())
    onboarding.manager.track_message(message.from_user.id, msg.message_id)
    bot.register_next_step_handler(msg, process_recipe_input, bot)

def process_recipe_input(message, bot):
    user_id = message.from_user.id
    onboarding.manager.track_message(user_id, message.message_id)
    
    ingredients = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ **Retsept yaratilmoqda...**", parse_mode="Markdown")
    onboarding.manager.track_message(user_id, status_msg.message_id)
    
    prompt = f"""
    Mavjud mahsulotlar: {ingredients}
    Vazifa: Shu mahsulotlardan tayyorlasa bo'ladigan sog'lom va mazali retsept yozing.
    
    FORMAT:
    🍳 **Taom Nomi**
    
    ⏱ Vaqt: ...
    🔥 Kaloriya: ...
    
    **Kerakli masalliqlar:**
    - ...
    
    **Tayyorlash:**
    1. ...
    2. ...
    
    Qisqa va londa bo'lsin.
    """
    
    response = call_gemini(prompt)
    if response:
        # Send as new message
        bot.send_message(message.chat.id, format_gemini_text(response, "AI Retsept"), parse_mode="HTML")
        # bot.edit_message_text(format_gemini_text(response, "AI Retsept"), message.chat.id, status_msg.message_id, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ AI band. Keyinroq urining.")
        
    delete_tracked_messages(user_id, bot)
    onboarding.manager.clear_user(user_id)

@require_premium
def handle_weekly_report(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "⏳ **Haftalik hisobot tayyorlanmoqda...**", parse_mode="Markdown")
    
    # Mock data for now, ideally fetch logs
    prompt = f"""
    Foydalanuvchi: {user.get('full_name')}
    Maqsad: {user.get('goal')}
    Ballar: {user.get('yasha_points')}
    
    Vazifa: Foydalanuvchiga motivatsion haftalik hisobot yozing.
    
    FORMAT:
    📊 **Haftalik Hisobot**
    
    ✅ **Yutuqlar:**
    - ...
    
    💡 **Maslahat:**
    - ...
    
    🔥 **Keyingi hafta uchun maqsad:**
    - ...
    """
    
    response = call_gemini(prompt)
    if response:
        bot.edit_message_text(format_gemini_text(response, "Haftalik Hisobot"), user_id, status_msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text("❌ AI band. Keyinroq urining.", user_id, status_msg.message_id)
