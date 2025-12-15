
import time
import threading
import schedule
from scripts.backup_db import create_backup
from core.observability import log_event
from bot.retention import run_retention_check

def run_backup_job():
    print("⏰ Scheduled Backup Starting...")
    success = create_backup()
    log_event(
        event_type="system_backup",
        success=success,
        meta={"source": "scheduler"}
    )

def start_backup_scheduler(bot=None):
    # Run every day at 03:00
    schedule.every().day.at("03:00").do(run_backup_job)
    
    # Retention Job (10:00 AM)
    if bot:
        schedule.every().day.at("10:00").do(run_retention_check, bot)
    
    # Also run once on startup for Verification? No, that might slow down startup.
    # User asked for "Smoke test checklist" implying visual verification.
    
    def loop():
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
