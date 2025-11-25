import os
import telebot
from dotenv import load_dotenv
from core.db import db
from bot.handlers import register_all_handlers
from bot.reminders import start_reminder_thread

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in .env file.")
    exit(1)

# Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN)

def main():
    print("🚀 Fitness AI Bot ishga tushmoqda...")
    
    # Initialize Database
    db.init_db()
    print("✅ Database ulandi.")
    
    # Register Handlers
    register_all_handlers(bot)
    print("✅ Handlerlar yuklandi.")
    
    # Start Reminder Thread
    start_reminder_thread(bot)
    print("✅ Eslatmalar xizmati ishga tushdi.")
    
    # Start Polling
    print("🤖 Bot ishlamoqda...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot to‘xtadi: {e}")

if __name__ == "__main__":
    main()
