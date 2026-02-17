import os
from dotenv import load_dotenv

load_dotenv()

# App Config
SHOP_ID = int(os.getenv("SHOP_ID", "1"))
TIMEZONE = "Asia/Tashkent"
LANGUAGES = ["uz", "ru"]

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_TELEGRAM_IDS = [int(x.strip()) for x in os.getenv("OWNER_TELEGRAM_IDS", "").split(",") if x.strip()]
