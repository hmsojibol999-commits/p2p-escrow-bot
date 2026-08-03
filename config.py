import os
from dotenv import load_dotenv

load_dotenv()

# Environment Variables Validation
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN environment variable is missing or empty.")

owner_id_str = os.getenv("OWNER_ID")
if not owner_id_str:
    raise ValueError("Error: OWNER_ID environment variable is missing or empty.")
OWNER_ID: int = int(owner_id_str)

support_admin_id_str = os.getenv("SUPPORT_ADMIN_ID")
if not support_admin_id_str:
    raise ValueError("Error: SUPPORT_ADMIN_ID environment variable is missing or empty.")
SUPPORT_ADMIN_ID: int = int(support_admin_id_str)

REQUIRED_CHANNEL_1 = os.getenv("REQUIRED_CHANNEL_1")
if not REQUIRED_CHANNEL_1:
    raise ValueError("Error: REQUIRED_CHANNEL_1 environment variable is missing or empty.")

REQUIRED_CHANNEL_2 = os.getenv("REQUIRED_CHANNEL_2")
if not REQUIRED_CHANNEL_2:
    raise ValueError("Error: REQUIRED_CHANNEL_2 environment variable is missing or empty.")

port_str = os.getenv("PORT", "8080")
PORT: int = int(port_str)

# Wallet Configuration Constants
MIN_DEPOSIT: float = 50.0
MIN_WITHDRAW: float = 100.0

# Marketplace Configuration Constants
DEFAULT_CURRENCY: str = "BDT"
MAX_PRODUCT_TITLE_LENGTH: int = 100
MAX_CATEGORY_NAME_LENGTH: int = 50
MAX_TXT_IMPORT_SIZE: int = 5 * 1024 * 1024  # 5 MB

# Bot Configuration Constants
BOT_NAME: str = "Digital Marketplace Bot"
BOT_VERSION: str = "1.0.0"

SUPPORT_RESPONSE_TEXT: str = (
    "📞 **সাপোর্ট সেন্টার**\n\n"
    "আপনার যেকোনো সমস্যা বা প্রয়োজনে আমাদের অ্যাডমিনের সাথে যোগাযোগ করুন:\n"
    "অ্যাডমিন: @AdminUsername\n\n"
    "দয়া করে আপনার সমস্যা বিস্তারিত জানান।"
)

SELLER_INFO_TEXT: str = (
    "🛒 **সেলার ইনফরমেশন**\n\n"
    "আমাদের প্ল্যাটফর্মে সেলার হতে চাইলে নিচের নিয়মগুলো মেনে চলুন:\n"
    "১. সঠিক পণ্য সরবরাহ করুন।\n"
    "২. কোনো রকম ভুয়া বা স্ক্যাম পণ্য বিক্রি করা যাবে না।\n"
    "৩. নিয়মের বাইরে গেলে অ্যাকাউন্ট স্থায়ীভাবে ব্যান করা হবে।"
)
