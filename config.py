import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
SUPPORT_ADMIN_ID = int(os.getenv("SUPPORT_ADMIN_ID", 0))

REQUIRED_CHANNEL_1 = os.getenv("REQUIRED_CHANNEL_1", "")
REQUIRED_CHANNEL_2 = os.getenv("REQUIRED_CHANNEL_2", "")

PORT = int(os.getenv("PORT", 10000))

# Business Configurations
MIN_DEPOSIT = 50.0  # BDT
MIN_WITHDRAW = 200.0  # BDT

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")
    
