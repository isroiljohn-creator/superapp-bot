import os
from dotenv import load_dotenv

load_dotenv()

# Bot Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Admin
# Parse ADMIN_ID (single) and ADMIN_IDS (comma separated list)
MAIN_ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip().isdigit()]
if MAIN_ADMIN_ID and MAIN_ADMIN_ID not in ADMIN_IDS:
    ADMIN_IDS.append(MAIN_ADMIN_ID)

# Payment
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

# Premium Prices (in tiyin)
PRICE_1_MONTH = 4900000 # 49,000 UZS
PRICE_3_MONTHS = 11900000 # 119,000 UZS
