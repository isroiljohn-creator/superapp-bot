import uuid
import time
import os
from telebot import types
from core.db import db
from bot.keyboards import main_menu_keyboard
from dotenv import load_dotenv

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Payment details (Mock)
PAYMENT_CARDS = {
    "click": "8600 0000 0000 0000 (Click)",
    "payme": "9860 0000 0000 0000 (Payme)",
    "uzum": "4400 0000 0000 0000 (Uzum)"
}

def handle_premium_menu(message, bot, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        return

    points = user['points']
    is_premium = db.is_premium(user_id)
    
    until_date = "Yo‘q"
    if is_premium and user['is_premium_until']:
        until_date = user['is_premium_until'][:10]
        
    premium_status = "✅ Aktiv" if is_premium else "❌ Yo‘q"
    
    text = (
        f"💎 **Premium Bo'limi**\n\n"
        f"💰 Ballaringiz: **{points}**\n"
        f"🌟 Premium holati: {premium_status}\n"
        f"📅 Premium tugash sanasi: {until_date}\n\n"
        "💎 **Premium tariflar:**\n"
        "• 1 oy: 49 000 so'm\n"
        "• 3 oy: 119 000 so'm\n\n"
        "⚠️ **Diqqat**: Premium obuna to'lovdan keyin avtomatik faollashadi.\n\n"
        "👇 Obuna sotib olish uchun pastdagi tugmalardan birini tanlang:"
    )
    
    markup = types.InlineKeyboardMarkup()
    # Removed free redemption option - only paid options now
    markup.add(types.InlineKeyboardButton("💳 1 oy — 49 000 so'm", callback_data="select_30"))
    markup.add(types.InlineKeyboardButton("💳 3 oy — 119 000 so'm", callback_data="select_90"))
    
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

def register_handlers(bot):
    # Free redemption option removed - premium now requires payment only
    # @bot.callback_query_handler(func=lambda call: call.data in ["redeem_7"])
    # def handle_redemption(call):
    #     ... (removed)

    @bot.callback_query_handler(func=lambda call: call.data in ["select_30", "select_90"])
    def handle_plan_selection(call):
        provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
        
        if not provider_token:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "⚠️ **To'lov tizimi hozircha sozlanmagan.**\n\n"
                "Iltimos, admin bilan bog'laning yoki keyinroq urinib ko'ring.\n\n"
                "📞 Qayta aloqa: @admin",
                parse_mode="Markdown"
            )
            return
        
        days = 30 if call.data == "select_30" else 90
        amount = 4900000 if call.data == "select_30" else 11900000 # Amount in tiyin (100 tiyin = 1 sum)
        title = f"Premium {days} kun"
        description = f"Fitness Bot Premium obunasi ({days} kun). Barcha imkoniyatlardan foydalaning!"
        payload = f"premium_{days}"
        currency = "UZS"
        prices = [types.LabeledPrice(label=title, amount=amount)]

        bot.send_invoice(
            call.message.chat.id,
            title=title,
            description=description,
            invoice_payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter="premium-sub",
            is_flexible=False
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.pre_checkout_query_handler(func=lambda query: True)
    def checkout(pre_checkout_query):
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    @bot.message_handler(content_types=['successful_payment'])
    def got_payment(message):
        user_id = message.from_user.id
        payment = message.successful_payment
        payload = payment.invoice_payload # e.g., premium_30
        
        days = int(payload.split("_")[1])
        amount = payment.total_amount / 100 # Convert back to UZS
        currency = payment.currency
        
        # Create order record
        order_id = f"pay_{payment.provider_payment_charge_id}"
        db.create_order(order_id, user_id, days, amount, currency)
        db.update_order_status(order_id, 'paid')
        
        # Activate Premium
        db.set_premium(user_id, days)
        
        bot.send_message(user_id, f"✅ **To'lov muvaffaqiyatli amalga oshirildi!**\n\nSizga {days} kunlik Premium obuna faollashtirildi. 🎉\nBarcha imkoniyatlardan foydalanishingiz mumkin!", parse_mode="Markdown")
        
        # Notify Admin
        if ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"💰 **Yangi To'lov!**\nUser: {message.from_user.first_name} (ID: {user_id})\nSumma: {amount} {currency}\nTarif: {days} kun")
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data == "back_premium")
    def back_to_premium(call):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_premium_menu(call.message, bot)

    # Admin manual confirm kept just in case
    @bot.message_handler(commands=['confirm_premium'])
    def admin_confirm_premium(message):
        if message.from_user.id != ADMIN_ID:
            return
        try:
            parts = message.text.split()
            order_id = parts[1]
            days = int(parts[2])
            
            order = db.get_order(order_id)
            if not order:
                bot.reply_to(message, "❌ Buyurtma topilmadi.")
                return
            
            db.update_order_status(order_id, 'paid')
            db.set_premium(order['user_id'], days)
            
            bot.reply_to(message, f"✅ To'lov tasdiqlandi! User {order['user_id']} ga {days} kun Premium berildi.")
        except Exception:
            pass
