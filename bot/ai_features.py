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
        msg = bot.send_message(
            message.chat.id, 
            "❓ **AI Murabbiy**\n\nMashg'ulotlar, ovqatlanish yoki sog'lom turmush tarzi bo'yicha istalgan savolingizni yozing:", 
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_ai_qa, bot)
    except Exception as e:
        print(f"Handle AI QA Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_ai_qa(message, bot):
    user_id = message.from_user.id
    question = message.text
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "🤖 **Javob tayyorlanmoqda...**", parse_mode="Markdown")
    
    prompt = f"""
    Siz professional fitnes murabbiyisiz.
    
    Foydalanuvchi Profili:
    - Yosh: {user.get('age')}
    - Jins: {user.get('gender')}
    - Bo'y: {user.get('height')} sm
    - Vazn: {user.get('weight')} kg
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    
    Foydalanuvchi savoli: "{question}"
    
    Vazifa: Savolga qisqa, aniq va foydalanuvchi profiliga moslashtirilgan javob bering.
    
    FORMAT:
    - Qisqa paragraflar.
    - Muhim joylari **qalin** harfda.
    - Ro'yxat (bullet points) ishlating.
    - O'zbek tilida.
    - HTML formatida (faqat <b>, <i>).
    """
    
    try:
        response = call_gemini(prompt)
        
        if response:
            try:
                bot.edit_message_text(format_gemini_text(response, "AI Javobi"), user_id, status_msg.message_id, parse_mode="HTML")
            except Exception:
                bot.edit_message_text(format_gemini_text(response, "AI Javobi"), user_id, status_msg.message_id, parse_mode=None)
        else:
            bot.edit_message_text("❌ AI band. Keyinroq urining.", user_id, status_msg.message_id)
            
    except Exception as e:
        print(f"AI QA Error: {e}")
        bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", user_id, status_msg.message_id)

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
        msg = bot.send_message(
            message.chat.id, 
            "🍳 **AI Retsept**\n\nMuzlatgichda bor mahsulotlarni yozing (masalan: tovuq, guruch, pomidor). Men sizga mos sog'lom retsept tuzib beraman:", 
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_recipe_input, bot)
    except Exception as e:
        print(f"Handle Recipe Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_recipe_input(message, bot):
    user_id = message.from_user.id
    ingredients = message.text
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(message.chat.id, "⏳ **Retsept yaratilmoqda...**", parse_mode="Markdown")
    
    prompt = f"""
    Siz professional dietolog va oshpazsiz.
    
    Foydalanuvchi Profili:
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    - Allergiya: {user.get('allergies')}
    
    Mavjud mahsulotlar: "{ingredients}"
    
    Vazifa: Shu mahsulotlardan foydalanib, foydalanuvchi maqsadiga mos 1-2 ta sog'lom va mazali retsept taklif qiling.
    
    SHARTLAR:
    - O'zbek milliy taomlariga moslashtirilgan bo'lsin.
    - Sog'lom va parhezbop bo'lsin.
    
    FORMAT:
    🍳 **Taom Nomi**
    
    📝 **Qisqa tavsif**
    
    ⏱ Vaqt: ... daqiqa
    🔥 Kaloriya: ... kkal
    📊 BJU: Oqsil ...g / Yog' ...g / Uglevod ...g
    
    🛒 **Kerakli masalliqlar:**
    - ...
    
    👨‍🍳 **Tayyorlash:**
    1. ...
    2. ...
    
    Qisqa, londa va ishtahaochar bo'lsin. HTML formatida (faqat <b>).
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
        bot.edit_message_text(f"❌ Xatolik: {str(e)[:100]}", message.chat.id, status_msg.message_id)

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
