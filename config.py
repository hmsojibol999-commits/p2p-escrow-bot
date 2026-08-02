# ==========================================================
# config.py
#
# Project Configuration Module
# Compatible with:
# Python 3.12
# Aiogram 3.x
# Pydantic v2
# Render Environment Variables
# ==========================================================

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Global application configuration.
    Loads values from .env file or Render Environment Variables.
    """

    # ======================================================
    # ENVIRONMENT
    # ======================================================

    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    BOT_USERNAME: str = Field("", description="Telegram Bot Username")

    DATABASE_URL: str = Field(..., description="PostgreSQL Database URL")

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    OWNER_ID: int = Field(..., description="Main Owner Telegram ID")
    SUPPORT_ADMIN_ID: int = Field(..., description="Support Admin Telegram ID")

    SECRET_KEY: str = Field(..., description="Security Secret Key")

    REQUIRED_CHANNEL: str = Field(
        "",
        description="Force subscription channel"
    )


    # ======================================================
    # ROLE SETTINGS
    # ======================================================

    ROLE_OWNER: str = "OWNER"
    ROLE_SUPPORT_ADMIN: str = "SUPPORT_ADMIN"
    ROLE_USER: str = "USER"


    # ======================================================
    # DATABASE
    # ======================================================

    DB_POOL_SIZE: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_AUTO_RECONNECT: bool = True
    DB_ECHO: bool = False


    # ======================================================
    # BOT SETTINGS
    # ======================================================

    PARSE_MODE: str = "HTML"

    DEFAULT_LANGUAGE: str = "bn"

    SUPPORTED_LANGUAGES: List[str] = [
        "bn",
        "en"
    ]

    TIMEZONE: str = "Asia/Dhaka"


    # ======================================================
    # MARKETPLACE
    # ======================================================

    MARKETPLACE_NAME: str = "Digital Marketplace"

    CURRENCY: str = "BDT"

    DEFAULT_COMMISSION_PERCENT: float = 5.0

    MIN_DEPOSIT: float = 50.0

    MIN_WITHDRAW: float = 100.0

    MAX_WITHDRAW: float = 25000.0

    MAX_PRODUCT_UPLOAD_SIZE_MB: int = 50

    MAX_FILE_SIZE_MB: int = 100


    ALLOWED_FILE_EXTENSIONS: List[str] = [
        "zip",
        "rar",
        "txt",
        "pdf",
        "jpg",
        "png",
        "json"
    ]


    # ======================================================
    # WALLET
    # ======================================================

    WALLET_ENABLED: bool = True

    BALANCE_TRANSFER_ENABLED: bool = True

    DEPOSIT_ENABLED: bool = True

    WITHDRAW_ENABLED: bool = True


    # ======================================================
    # PAYMENT METHODS
    # ======================================================

    PAYMENT_BKASH_ENABLED: bool = True

    PAYMENT_NAGAD_ENABLED: bool = True

    PAYMENT_ROCKET_ENABLED: bool = False

    PAYMENT_BINANCE_PAY_ENABLED: bool = True

    PAYMENT_USDT_TRC20_ENABLED: bool = True

    PAYMENT_USDT_BEP20_ENABLED: bool = True

    PAYMENT_USDT_SOLANA_ENABLED: bool = False


    # ======================================================
    # SECURITY
    # ======================================================

    LOGIN_PIN_LENGTH: int = 4

    MAX_WRONG_PIN_ATTEMPTS: int = 3

    TEMPORARY_LOCK_TIME_MINUTES: int = 15

    SESSION_TIMEOUT_MINUTES: int = 60

    RATE_LIMIT_MESSAGES_PER_SEC: float = 1.5

    MAX_LOGIN_ATTEMPTS: int = 5


    # ======================================================
    # ESCROW
    # ======================================================

    ESCROW_ENABLED: bool = True

    ESCROW_AUTO_RELEASE_HOURS: int = 24

    ESCROW_DISPUTE_TIME_LIMIT_HOURS: int = 48

    ESCROW_AUTO_CANCEL_HOURS: int = 12


    # ======================================================
    # REFERRAL
    # ======================================================

    REFERRAL_ENABLED: bool = True

    REFERRAL_BONUS_ENABLED: bool = True

    DEFAULT_REFERRAL_BONUS_AMOUNT: float = 10.0


    # ======================================================
    # RATING
    # ======================================================

    RATING_ENABLED: bool = True

    MIN_RATING: int = 1

    MAX_RATING: int = 5


    # ======================================================
    # LOGGING
    # ======================================================

    LOG_FILE_NAME: str = "bot.log"

    CONSOLE_LOGGING: bool = True

    FILE_LOGGING: bool = True


    # ======================================================
    # PRODUCTION
    # ======================================================

    IS_PRODUCTION: bool = True


    # ======================================================
    # PYDANTIC CONFIG
    # ======================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global config object
config = Config()
