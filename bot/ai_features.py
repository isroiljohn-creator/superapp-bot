from telebot import types
from core.ai import call_gemini, format_gemini_text
from core.db import db

from bot.keyboards import ai_menu_keyboard

def handle_ai_tools_menu(message, bot):
    bot.send_message(
        message.chat.id,
        "🎯 **Shaxsiy Murabbiy**\n\nQanday yordam bera olaman?",
        reply_markup=ai_menu_keyboard(),
        parse_mode="Markdown"
    )

def handle_ai_qa(message, bot):
    msg = bot.send_message(message.chat.id, "❓ **Savolingizni yozing:**", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_ai_qa, bot)

def process_ai_qa(message, bot):
    question = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ **O'ylayapman...**", parse_mode="Markdown")
    
    prompt = f"Siz fitnes murabbiyisiz. Savolga qisqa va aniq javob bering (o'zbek tilida): {question}"
    response = call_gemini(prompt)
    
    if response:
        bot.edit_message_text(format_gemini_text(response, "Savolga Javob"), message.chat.id, status_msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text("❌ AI band. Keyinroq urining.", message.chat.id, status_msg.message_id)

def handle_shopping_list(message, bot):
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

def handle_recipe_gen(message, bot):
    msg = bot.send_message(message.chat.id, "🍳 **Muzlatgichda nima bor?**\n\nMahsulotlarni yozing (masalan: tuxum, pomidor, pishloq), men retsept tuzib beraman:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_recipe_input, bot)

def process_recipe_input(message, bot):
    ingredients = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ **Retsept yaratilmoqda...**", parse_mode="Markdown")
    
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
        bot.edit_message_text(format_gemini_text(response, "AI Retsept"), message.chat.id, status_msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text("❌ AI band. Keyinroq urining.", message.chat.id, status_msg.message_id)

def handle_weekly_report(message, bot):
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
