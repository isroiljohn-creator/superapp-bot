import time
import threading
import schedule
from core.db import db

def send_daily_reminders(bot):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().weekday() # 0 = Monday, 6 = Sunday
    
    # Varied messages for each day of the week
    templates = [
        "☀️ Salom {name}! Yangi hafta muborak! Bugun suv ichdingizmi va mashqlarni qildingizmi? 💧💪\n\n/start tugmasini bosib vazifalarni tekshiring!",
        "☀️ Salom {name}! Sog'lig'ingizga e'tiborli bo'lishni unutmang. Suv ichdingizmi va mashqlarni bajardingizmi? 💧💪\n\n/start orqali tekshiring!",
        "☀️ Salom {name}! Haftaning o'rtasi keldi. Suv va mashqlar rejada bormi? 💧💪\n\n/start tugmasini bosing!",
        "☀️ Salom {name}! Maqsadingiz sari intilishda davom eting! Bugun suv va mashqlar qanday bo'ldi? 💧💪\n\n/start tugmasi sizni kutmoqda!",
        "☀️ Salom {name}! Bugungi suv ichish va mashg'ulotlar haqida unutmang, sog'lig'ingiz o'z qo'lingizda! 💧💪\n\n/start ni bosib belgilang!",
        "☀️ Salom {name}! Dam olish kuningiz unumli o'tsin. Bugun ham suv va mashqlar esingizdami? 💧💪\n\n/start orqali tekshiring!",
        "☀️ Salom {name}! Yakshanba - o'z ustingizda ishlash uchun yaxshi kun. Suv ichdingizmi va mashqlarni qildingizmi? 💧💪\n\n/start ni bosing!"
    ]
    
    template = templates[weekday]
    users = db.get_active_users()
    count = 0
    
    for user in users:
        try:
            user_id = user[0]
            full_name = user[1]
            username = user[2]
            
            # Check if reminder already sent today
            if db.check_reminder_sent(user_id, today):
                continue

            # Mark sent BEFORE sending to prevent race conditions (Double/Triple sends)
            db.mark_reminder_sent(user_id, today)
            
            name = full_name if full_name else (username if username else "Aziz foydalanuvchi")
            msg = template.format(name=name)
            
            bot.send_message(user_id, msg)
            count += 1
            
            # Anti-flood delay
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Failed to send reminder to {user[0]}: {e}")
            if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                db.update_user_profile(user[0], active=False)
    
    print(f"Daily reminders sent to {count} users.")

def init_reminder_schedule(bot):
    """Initializes the reminder schedule but does not start the thread."""
    # Schedule daily reminder at 09:00
    schedule.every().day.at("09:00").do(send_daily_reminders, bot)
    print("✅ Eslatmalar xizmati rejalashtirildi (09:00).")
