import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class to load and manage environment variables securely.
    """
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    def __init__(self) -> None:
        self.validate()

    @classmethod
    def validate(cls) -> None:
        """
        Validates that all essential environment variables are present.
        Raises a ValueError with a clear message if any required variable is missing.
        """
        if not cls.BOT_TOKEN:
            raise ValueError(
                "Error: Required environment variable 'BOT_TOKEN' is missing. "
                "Please check your .env file or Render deployment settings."
            )

# Instantiate and validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(e)
    exit(1)
    
