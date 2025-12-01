from bot.profile import handle_profile
from core.db import db
from unittest.mock import MagicMock

# Mock bot
bot = MagicMock()
bot.send_message = MagicMock()

# Mock message
message = MagicMock()
message.from_user.id = 987654321
message.chat.id = 987654321

# Ensure user exists in DB with special chars
db.add_user(987654321, "bad_user", "9999999")
db.update_user_profile(987654321, full_name="John_Doe_Test", goal="Lose_Weight")

print("Testing handle_profile with special chars...")
try:
    handle_profile(message, bot)
    print("handle_profile executed successfully.")
except Exception as e:
    print(f"Caught exception outside: {e}")

# Check what send_message was called with
if bot.send_message.called:
    args, kwargs = bot.send_message.call_args
    print(f"bot.send_message called with: {args}")
    text = args[1]
    if "John\\_Doe\\_Test" in text:
        print("SUCCESS: Name was escaped correctly.")
    else:
        print("FAILURE: Name was NOT escaped.")
else:
    print("bot.send_message was NOT called.")
