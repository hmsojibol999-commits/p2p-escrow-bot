import os
from dotenv import load

load_dotenv()

def get_env(key: str, default: str = None, required: bool = False) -> str:
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Environment variable {key} is required but not set.")
    return value

def get_env_int(key: str, default: int = None, required: bool = False) -> int:
    value = os.getenv(key)
    if value is None:
        if required:
            raise ValueError(f"Environment variable {key} is required but not set.")
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be an integer, got '{value}'.")

def get_env_float(key: str, default: float = None, required: bool = False) -> float:
    value = os.getenv(key)
    if value is None:
        if required:
            raise ValueError(f"Environment variable {key} is required but not set.")
        return default
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be a float, got '{value}'.")

# Telegram Configuration
BOT_TOKEN: str = get_env("BOT_TOKEN", required=True)

# Admin Configuration
OWNER_ID: int = get_env_int("OWNER_ID", required=True)
SUPPORT_ADMIN_ID: int = get_env_int("SUPPORT_ADMIN_ID", required=True)

# Force Join Configuration
REQUIRED_CHANNEL_1: str = get_env("REQUIRED_CHANNEL_1", required=True)
REQUIRED_CHANNEL_2: str = get_env("REQUIRED_CHANNEL_2", required=True)

# Deposit & Withdraw Configuration
MIN_DEPOSIT: float = get_env_float("MIN_DEPOSIT", required=True)
MIN_WITHDRAW: float = get_env_float("MIN_WITHDRAW", required=True)

# Wallet Configuration
DEFAULT_BALANCE: float = get_env_float("DEFAULT_BALANCE", 0.0)

# Database Configuration
DATABASE_PATH: str = get_env("DATABASE_PATH", "data/market.db")

# Render Web Service Configuration
PORT: int = get_env_int("PORT", 10000)

# Bot Information
BOT_NAME: str = get_env("BOT_NAME", "MarketplaceBot")

# Logging Configuration
LOG_LEVEL: str = get_env("LOG_LEVEL", "INFO")
