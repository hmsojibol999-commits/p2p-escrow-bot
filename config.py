# ==========================================================
# P2P ESCROW MARKETPLACE BOT
#
# File    : config.py
# Module  : Global Configuration
# Version : V1.0.0
#
# Purpose :
# Central configuration loader for Render / Production
# Environment variables and bot settings.
# ==========================================================

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Production configuration manager.
    Loads values from environment variables or .env file.
    Compatible with Python 3.12 + Pydantic v2.
    """

    # ======================================================
    # Telegram Bot
    # ======================================================

    BOT_TOKEN: str = Field(
        ...,
        description="Telegram Bot Token"
    )

    BOT_USERNAME: str = Field(
        ...,
        description="Telegram Bot Username without @"
    )


    # ======================================================
    # Database
    # ======================================================

    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL Database URL"
    )


    DB_POOL_SIZE: int = Field(
        5,
        description="Database connection pool size"
    )

    DB_POOL_TIMEOUT: int = Field(
        20,
        description="Database pool timeout"
    )

    DB_ECHO: bool = Field(
        False,
        description="Enable SQL query logging"
    )


    # ======================================================
    # Admin / Security
    # ======================================================

    OWNER_ID: int = Field(
        ...,
        description="Main owner Telegram ID"
    )


    SUPPORT_ADMIN_ID: int = Field(
        ...,
        description="Support admin Telegram ID"
    )


    SECRET_KEY: str = Field(
        ...,
        description="Application secret key"
    )


    MAX_WRONG_PIN_ATTEMPTS: int = Field(
        3
    )


    PIN_LOCK_TIME_MINUTES: int = Field(
        15
    )


    # ======================================================
    # Bot Settings
    # ======================================================

    PARSE_MODE: str = "HTML"

    DEFAULT_LANGUAGE: str = "bn"

    SUPPORTED_LANGUAGES: List[str] = Field(
        default_factory=lambda: [
            "bn",
            "en"
        ]
    )

    TIMEZONE: str = "Asia/Dhaka"



    # ======================================================
    # Marketplace
    # ======================================================

    MARKETPLACE_NAME: str = "P2P Digital Marketplace"

    CURRENCY: str = "BDT"


    DEFAULT_COMMISSION_PERCENT: float = 5.0


    MIN_DEPOSIT: float = 50.0


    MIN_WITHDRAW: float = 100.0


    MAX_WITHDRAW: float = 25000.0



    # ======================================================
    # Wallet System
    # ======================================================

    WALLET_ENABLED: bool = True

    DEPOSIT_ENABLED: bool = True

    WITHDRAW_ENABLED: bool = True

    TRANSFER_ENABLED: bool = True



    # ======================================================
    # Payment Gateway Flags
    # ======================================================

    PAYMENT_BKASH_ENABLED: bool = True

    PAYMENT_NAGAD_ENABLED: bool = True

    PAYMENT_ROCKET_ENABLED: bool = False

    PAYMENT_BINANCE_PAY_ENABLED: bool = True

    PAYMENT_USDT_ENABLED: bool = True



    # ======================================================
    # Escrow
    # ======================================================

    ESCROW_ENABLED: bool = True


    ESCROW_AUTO_RELEASE_HOURS: int = 24


    ESCROW_DISPUTE_LIMIT_HOURS: int = 48



    # ======================================================
    # Channel Subscription
    # ======================================================

    REQUIRED_CHANNEL: str = ""



    # ======================================================
    # Logging
    # ======================================================

    LOG_LEVEL: str = "INFO"

    LOG_FILE_NAME: str = "bot.log"


    # ======================================================
    # Environment
    # ======================================================

    DEBUG: bool = False

    IS_PRODUCTION: bool = True



    # ======================================================
    # Pydantic Config
    # ======================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )



# ==========================================================
# Global Config Instance
# ==========================================================

Config = Settings()
