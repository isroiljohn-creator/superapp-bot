from telebot import types
from core.ai import call_gemini, format_gemini_text
from core.db import db
from bot.premium import require_premium

from bot.keyboards import ai_inline_keyboard

def handle_ai_tools_menu(message, bot):
    bot.send_message(
        message.chat.id,
        "🎯 **Shaxsiy Murabbiy**\n\nQanday yordam bera olaman?",
        reply_markup=ai_inline_keyboard(),
        parse_mode="Markdown"
    )

@require_premium
def handle_ai_qa(message, bot):
    try:
        msg = bot.send_message(message.chat.id, "❓ Savolingizni yozing:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_ai_qa, bot)
    except Exception as e:
        print(f"Handle AI QA Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_ai_qa(message, bot):
    user_id = message.from_user.id
    question = message.text
    
    status_msg = bot.send_message(user_id, "🤖 **Javob tayyorlanmoqda...**", parse_mode="Markdown")
    
    try:
        # Use the centralized function from core.ai
        from core.ai import ai_answer_question
        answer = ai_answer_question(question)
        
        if answer:
            try:
                bot.edit_message_text(answer, user_id, status_msg.message_id, parse_mode="HTML")
            except Exception as e:
                # Fallback if HTML parsing fails
                bot.edit_message_text(answer, user_id, status_msg.message_id, parse_mode=None)
        else:
            bot.edit_message_text("❌ AI band. Keyinroq urining.", user_id, status_msg.message_id)
            
    except Exception as e:
        print(f"AI QA Error: {e}")
        bot.edit_message_text("❌ Xatolik yuz berdi.", user_id, status_msg.message_id)

@require_premium
def handle_shopping_list(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "⏳ **AI xaridlar ro'yxatini tuzmoqda...**", parse_mode="Markdown")
    
    from core.ai import ai_generate_shopping_list
    
    response = ai_generate_shopping_list(user)
    
    if response:
        try:
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode=None)
    else:
        bot.edit_message_text("❌ AI band. Keyinroq urining.", user_id, status_msg.message_id)

@require_premium
def handle_recipe_gen(message, bot):
    try:
        msg = bot.send_message(message.chat.id, "🍳 **Muzlatgichda nima bor?**\n\nMahsulotlarni yozing (masalan: tuxum, pomidor, pishloq), men retsept tuzib beraman:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_recipe_input, bot)
    except Exception as e:
        print(f"Handle Recipe Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_recipe_input(message, bot):
    ingredients = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ **Retsept yaratilmoqda...**", parse_mode="Markdown")
    
    prompt = f"""
    Mavjud mahsulotlar: {ingredients}
    Vazifa: Shu mahsulotlardan tayyorlasa bo'ladigan sog'lom va mazali retsept yozing.
    
    📌 SHARTLAR:
    - O'zbek milliy taomlariga yaqin bo'lsa yaxshi.
    - Sog'lom va parhezbop bo'lsin.
    
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
    
    try:
        response = call_gemini(prompt)
        if response:
            try:
                bot.edit_message_text(format_gemini_text(response, "AI Retsept"), message.chat.id, status_msg.message_id, parse_mode="HTML")
            except Exception:
                bot.edit_message_text(format_gemini_text(response, "AI Retsept"), message.chat.id, status_msg.message_id, parse_mode=None)
        else:
            bot.edit_message_text("❌ AI band. Keyinroq urining.", message.chat.id, status_msg.message_id)
    except Exception as e:
        print(f"Recipe Error: {e}")
        bot.edit_message_text("❌ Xatolik yuz berdi.", message.chat.id, status_msg.message_id)

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
