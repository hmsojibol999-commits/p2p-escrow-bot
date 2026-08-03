import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class to load and manage environment variables securely.
    """
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    API_ID: str = os.getenv("API_ID")
    API_HASH: str = os.getenv("API_HASH")

    def __init__(self):
        self.validate()

    @classmethod
    def validate(cls):
        """
        Validates that all essential environment variables are present.
        Raises a ValueError with a clear message if any required variable is missing.
        """
        missing_vars = []
        
        if not cls.BOT_TOKEN:
            missing_vars.append("BOT_TOKEN")
        if not cls.API_ID:
            missing_vars.append("API_ID")
        if not cls.API_HASH:
            missing_vars.append("API_HASH")

        if missing_vars:
            raise ValueError(
                f"Error: Required environment variable(s) missing: {', '.join(missing_vars)}. "
                "Please check your .env file or deployment settings."
            )

# Instantiate and validate configuration
try:
    Config.validate()
except ValueError as e:
    print(e)
    exit(1)
