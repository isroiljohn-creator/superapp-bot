from core.db import db

def handle_referral(message, bot):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        bot.send_message(user_id, "Iltimos, avval /start ni bosing.")
        return

    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    ref_count = db.get_referral_count(user_id)
    
    text = (
        f"🔗 **Sizning referal havolangiz:**\n{ref_link}\n\n"
        f"👥 Taklif qilgan do‘stlaringiz: {ref_count} ta\n"
        f"💎 Ballaringiz: {user['points']}\n\n"
        "Har bir do‘stingiz uchun +1 ball olasiz. 5 ta do‘stingizni taklif qilsangiz, 7 kunlik Premium bepul beriladi!"
    )
    
    bot.send_message(user_id, text)
