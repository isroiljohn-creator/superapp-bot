from telebot import types
from core.ai import call_gemini, format_gemini_text
from core.db import db
from bot.premium import require_premium

from bot.keyboards import ai_inline_keyboard

def handle_ai_tools_menu(message, bot):
    bot.send_message(
        message.chat.id,
        "🎯 <b>Shaxsiy Murabbiy</b>\n\nQanday yordam bera olaman?",
        reply_markup=ai_inline_keyboard(),
        parse_mode="HTML"
    )

@require_premium
def handle_ai_qa(message, bot, user_id=None):
    try:
        msg = bot.send_message(
            message.chat.id, 
            "❓ <b>AI Murabbiy</b>\n\nMashg'ulotlar, ovqatlanish yoki sog'lom turmush tarzi bo'yicha istalgan savolingizni yozing:", 
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_ai_qa, bot)
    except Exception as e:
        print(f"Handle AI QA Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_ai_qa(message, bot):
    user_id = message.from_user.id
    question = message.text
    user = db.get_user(user_id)
    
    # Send "typing" action instead of message to avoid clutter, or keep message if preferred
    status_msg = bot.send_message(user_id, "🤖 <b>Javob tayyorlanmoqda...</b>", parse_mode="HTML")
    
    system_prompt = f"""
    Siz professional fitnes murabbiyisiz.
    
    Foydalanuvchi Profili:
    - Yosh: {user.get('age')}
    - Jins: {user.get('gender')}
    - Bo'y: {user.get('height')} sm
    - Vazn: {user.get('weight')} kg
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    
    Vazifa: Savolga qisqa, aniq va foydalanuvchi profiliga moslashtirilgan javob bering.
    
    FORMAT TALABLARI:
    - Maksimal 700-900 belgi.
    - Qisqa paragraflar.
    - Muhim joylari uchun <b>qalin</b> (HTML) ishlating.
    - Ro'yxat uchun tire (-) ishlating.
    - Markdown ishlata ko'rmang (* yoki _).
    - Faqat HTML teglar: <b>, <i>, <u>, <s>, <code>, <pre>.
    - O'zbek tilida.
    """
    
    try:
        from core.ai import ask_gemini
        response = ask_gemini(system_prompt, question)
        
        # Edit status message with response
        try:
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            # Fallback to plain text if HTML is invalid
            bot.edit_message_text(response, user_id, status_msg.message_id, parse_mode=None)
            
        # Send main menu to restore navigation
        from bot.keyboards import main_menu_keyboard
        bot.send_message(user_id, "Yana nima yordam bera olaman?", reply_markup=main_menu_keyboard())
            
    except Exception as e:
        print(f"AI QA Error: {e}")
        bot.edit_message_text("AI hozircha javob bera olmadi. Birozdan keyin yana urinib ko‘ring 🙂", user_id, status_msg.message_id)

@require_premium
def handle_shopping_list(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "⏳ <b>AI xaridlar ro'yxatini tuzmoqda...</b>", parse_mode="HTML")
    
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
def handle_recipe_gen(message, bot, user_id=None):
    try:
        msg = bot.send_message(
            message.chat.id, 
            "🍳 <b>AI Retsept</b>\n\nMuzlatgichda bor mahsulotlarni yozing (masalan: tovuq, guruch, pomidor). Men sizga mos sog'lom retsept tuzib beraman:", 
            reply_markup=types.ForceReply(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_recipe_input, bot)
    except Exception as e:
        print(f"Handle Recipe Error: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

def process_recipe_input(message, bot):
    user_id = message.from_user.id
    ingredients = message.text
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(message.chat.id, "⏳ <b>Retsept yaratilmoqda...</b>", parse_mode="HTML")
    
    system_prompt = f"""
    Siz professional dietolog va oshpazsiz.
    
    Foydalanuvchi Profili:
    - Maqsad: {user.get('goal')}
    - Faollik: {user.get('activity_level')}
    - Allergiya: {user.get('allergies')}
    
    Vazifa: Foydalanuvchi kiritgan mahsulotlardan foydalanib, uning maqsadiga mos 1 ta sog'lom va mazali retsept taklif qiling.
    
    FORMAT TALABLARI:
    - Maksimal 900 belgi.
    - Markdown ishlata ko'rmang (* yoki _).
    - Faqat HTML teglar: <b>, <i>.
    - Struktura:
      * <b>Taom Nomi</b>
      * <b>Masalliqlar</b> (Ro'yxat)
      * <b>Tayyorlash</b> (3-6 qadam)
      * <b>Foydali maslahat</b> (1 gap)
    - O'zbek tilida.
    """
    
    try:
        from core.ai import ask_gemini
        response = ask_gemini(system_prompt, ingredients)
        
        try:
            bot.edit_message_text(response, message.chat.id, status_msg.message_id, parse_mode="HTML")
        except Exception:
            bot.edit_message_text(response, message.chat.id, status_msg.message_id, parse_mode=None)
            
        # Send main menu to restore navigation
        from bot.keyboards import main_menu_keyboard
        bot.send_message(user_id, "Yana nima yordam bera olaman?", reply_markup=main_menu_keyboard())
            
    except Exception as e:
        print(f"Recipe Error: {e}")
        bot.edit_message_text("AI hozir retsept tuza olmadi. Mahsulotlar ozroq bo‘lishi yoki tarmoqda muammo bo‘lishi mumkin. Birozdan keyin yana urinib ko‘ring 🙂", message.chat.id, status_msg.message_id)

@require_premium
def handle_weekly_report(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    status_msg = bot.send_message(user_id, "⏳ <b>Haftalik hisobot tayyorlanmoqda...</b>", parse_mode="HTML")
    
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
