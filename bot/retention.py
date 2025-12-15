
import datetime
from core.db import db
from core.flags import is_flag_enabled
from core.context import get_founder_tone_prompt

def run_retention_check(bot):
    """
    Scheduled job to check for inactive users and send nudges.
    """
    # 1. Global Safety Check
    # We can check a global flag first, or check per user.
    # Let's check a "global" switch using a dummy key or just 'retention_engine' without user_id first for efficiency?
    # Actually flags are usually per user. But for a cron job, we can check "if feature is globally enabled or rollout > 0".
    # For simplicity, we'll check inside the loop OR check if it's completely disabled.
    
    # Simple optimization: If flag is completely OFF (enabled=False, rollout=0), abort.
    # flag = db.get_feature_flag("retention_engine")
    # if not flag or (not flag['enabled'] and flag['rollout_percent'] <= 0):
    #    return

    print("Running Retention Check...")
    
    try:
        # 2. Get Candidates (This requires a DB query we might not have yet)
        # ideally: SELECT * FROM users WHERE last_active_date = NOW - INTERVAL '3 days'
        # Since we might not have an efficient index on last_active, we have to be careful.
        # MVP: We can iterate generic "active users" or we need a new DB method `get_inactive_users(days)`.
        
        # Let's Add `get_users_inactive_since(date)` to DB or just simple logic here.
        # If we can't query efficiently, we might skip or do a small batch.
        
        # Assuming we can't change DB schema/indexes easily (Rule 3).
        # We can iterate `get_active_users()`? No, those are active.
        # We need users who are NOT active.
        
        # Let's use `updated_at` from `users` table if available.
        # If not, we rely on `daily_logs`.
        
        # For this MVP task without changing generic helpers too much:
        # Let's rely on a new DB helper `get_users_by_inactivity(days)` which we will add to DB class (Safety Rule 5 allows new helpers).
        
        days_triggers = [3, 7, 10, 14]
        
        for days in days_triggers:
            users = db.get_users_inactive_for(days) # We need to implement this Additive helper
            
            for user in users:
                user_id = user['telegram_id']
                name = user['full_name']
                
                # Double check flag per user (Rollout support)
                if not is_flag_enabled("retention_engine", user_id):
                    continue
                    
                # Send Message
                send_retention_message(bot, user_id, name, days)
                
    except Exception as e:
        print(f"Retention Check Error: {e}")

def send_retention_message(bot, user_id, name, days):
    """
    Sends the specific message for the day.
    """
    try:
        msg = ""
        if days == 3:
            msg = f"👋 Salom {name}, ko'rinmay qoldingiz? Kichik qadamlar katta natijaga olib keladi. Bugun 5 daqiqa ajrata olamizmi?"
        elif days == 7:
            msg = f"Hafta o'tib ketdi, {name}. 📉 Ko'pchilik shu nuqtada tashlab ketadi. Siz ulardan emassiz. Qaytish uchun bitta tugmani bosish kifoya."
        elif days == 10:
            msg = f"{name}, rostini aytaman - formadan chiqish oson, qaytish qiyin. Lekin imkon bor. Bugun shunchaki suv ichishni belgilang, yetarli."
        elif days == 14:
            msg = f"2 hafta bo'ldi... 😔 Men hali ham shu yerdaman. Sizning maqsadingiz ham shu yerdami? Kel, bugun yangidan boshlaymiz."
            
        if msg:
            # Founder Tone Check?
            if is_flag_enabled("founder_tone", user_id):
                # Make it more direct? The above are already quite "Coach-like".
                pass
                
            bot.send_message(user_id, msg)
            # Log it
            from core.observability import log_event
            log_event("retention_sent", user_id=user_id, meta={"days": days})
            
    except Exception as e:
        print(f"Failed to send retention to {user_id}: {e}")
