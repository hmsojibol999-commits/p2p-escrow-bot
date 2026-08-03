import os
from dotenv import load_dotenv

# Load .env (লোকাল ডেভেলপমেন্টের জন্য)
load_dotenv()

# ==========================
# Telegram
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

SUPPORT_ADMIN_ID = int(
    os.getenv("SUPPORT_ADMIN_ID", "0")
)

# ==========================
# Required Channels
# ==========================

REQUIRED_CHANNEL_1 = os.getenv(
    "REQUIRED_CHANNEL_1", ""
).strip()

REQUIRED_CHANNEL_2 = os.getenv(
    "REQUIRED_CHANNEL_2", ""
).strip()

# ==========================
# Database
# ==========================

DATABASE_PATH = "data/market.db"

# ==========================
# Wallet Settings
# ==========================

MIN_DEPOSIT = 10
MIN_WITHDRAW = 1

# ==========================
# Bot Settings
# ==========================

BOT_NAME = "Marketplace Bot"

# ==========================
# Validation
# ==========================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing!"
    )

if OWNER_ID == 0:
    raise RuntimeError(
        "OWNER_ID environment variable is missing!"
    )

if SUPPORT_ADMIN_ID == 0:
    raise RuntimeError(
        "SUPPORT_ADMIN_ID environment variable is missing!"
    )
