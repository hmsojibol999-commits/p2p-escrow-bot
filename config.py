import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    def __init__(self):
        self.validate()

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("Error: BOT_TOKEN is missing. Please check your .env or Render settings.")

try:
    Config.validate()
except ValueError as e:
    print(e)
    exit(1)
    
