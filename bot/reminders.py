import time
import threading
import schedule
from core.db import db

def send_daily_reminders(bot):
    from datetime import datetime
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    weekday = now.weekday() # 0 = Monday, 6 = Sunday
    
    users = db.get_active_users_with_settings() # Need to implement this in db.py to fetch notification_settings
    count = 0
    
    for user in users:
        try:
            user_id = user[0]
            full_name = user[1]
            username = user[2]
            settings = user[3] # JSON notification_settings
            
            if not settings:
                # Default legacy behavior or ignore? Let's use default
                settings = {
                    "waterReminders": True,
                    "waterInterval": "2",
                    "workoutReminders": True,
                    "workoutTime": "09:00",
                    "sleepReminders": True,
                    "sleepTime": "22:00"
                }

            # 1. Workout Reminder (Time based)
            if settings.get("workoutReminders") and settings.get("workoutTime") == current_time:
                 if not db.check_specific_reminder_sent(user_id, today, "workout"):
                    lang = db.get_user_language(user_id)
                    name = full_name if full_name else (username if username else "Aziz foydalanuvchi")
                    from bot.languages import get_text
                    msg = "🏋️ " + get_text("reminder_workout_prompt", lang=lang, name=name)
                    bot.send_message(user_id, msg)
                    db.mark_specific_reminder_sent(user_id, today, "workout")
                    count += 1

            # 2. Daily General Reminder (Keep legacy logic as fallback/general at 09:00 if not workout)
            if current_time == "09:00":
                if db.check_reminder_sent(user_id, today):
                    continue

                db.mark_reminder_sent(user_id, today)
                lang = db.get_user_language(user_id)
                name = full_name if full_name else (username if username else "Aziz foydalanuvchi")
                key = f"reminder_day_{weekday}"
                from bot.languages import get_text
                msg = get_text(key, lang=lang, name=name)
                bot.send_message(user_id, msg)
                count += 1
            
            # Anti-flood delay
            time.sleep(0.04)
            
        except Exception as e:
            print(f"Failed to send reminder to {user[0]}: {e}")
            if "forbidden" in str(e).lower() or "blocked" in str(e).lower():
                db.update_user_profile(user[0], active=False)
    
    if count > 0:
        print(f"Daily reminders sent to {count} users.")

def init_reminder_schedule(bot):
    """Initializes the reminder schedule. Runs every minute to check for specific user times."""
    schedule.every(1).minutes.do(send_daily_reminders, bot)
    print("✅ Eslatmalar xizmati rejalashtirildi (Har minutda tekshirish).")
