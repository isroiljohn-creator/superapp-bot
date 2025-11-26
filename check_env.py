import os
from dotenv import load_dotenv

load_dotenv()

admin_id = os.getenv("ADMIN_ID")
bot_token = os.getenv("BOT_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"ADMIN_ID: {'SET (' + admin_id + ')' if admin_id else 'NOT SET'}")
print(f"BOT_TOKEN: {'SET' if bot_token else 'NOT SET'}")
print(f"GEMINI_API_KEY: {'SET' if gemini_key else 'NOT SET'}")

if admin_id and not admin_id.isdigit():
    print("WARNING: ADMIN_ID is not a number!")
