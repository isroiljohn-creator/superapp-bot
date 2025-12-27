import time
import threading
import schedule
from core.db import db

def send_daily_reminders(bot):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().weekday() # 0 = Monday, 6 = Sunday
    
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
            
            # Get user language
            lang = db.get_user_language(user_id)
            
            name = full_name if full_name else (username if username else "Aziz foydalanuvchi")
            key = f"reminder_day_{weekday}"
            from bot.languages import get_text
            msg = get_text(key, lang=lang, name=name)
            
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
