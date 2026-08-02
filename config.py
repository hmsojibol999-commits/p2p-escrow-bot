import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Production Configuration Manager.
    Compatible with:
    - Python 3.12
    - Pydantic v2
    - Render Environment Variables
    - .env file
    """

    # ==========================
    # Telegram Bot
    # ==========================
    BOT_TOKEN: str = Field(...)
    BOT_USERNAME: str = Field(default="")

    # ==========================
    # Database
    # ==========================
    DATABASE_URL: str = Field(...)

    DB_POOL_SIZE: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_ECHO: bool = Field(default=False)

    # ==========================
    # Owner / Admin
    # ==========================
    OWNER_ID: int = Field(...)
    SUPPORT_ADMIN_ID: int = Field(...)

    # ==========================
    # Security
    # ==========================
    SECRET_KEY: str = Field(...)

    LOGIN_PIN_LENGTH: int = Field(default=4)
    MAX_WRONG_PIN_ATTEMPTS: int = Field(default=3)
    TEMPORARY_LOCK_TIME_MINUTES: int = Field(default=15)

    # ==========================
    # Bot Settings
    # ==========================
    PARSE_MODE: str = Field(default="HTML")
    DEFAULT_LANGUAGE: str = Field(default="bn")

    SUPPORTED_LANGUAGES: List[str] = Field(
        default_factory=lambda: ["bn", "en"]
    )

    TIMEZONE: str = Field(
        default="Asia/Dhaka"
    )

    # ==========================
    # Channel Force Join
    # ==========================
    REQUIRED_CHANNEL: str = Field(default="")

    CHANNEL_1: str = Field(default="")
    CHANNEL_2: str = Field(default="")

    # ==========================
    # Marketplace
    # ==========================
    MARKETPLACE_NAME: str = Field(
        default="Digital Marketplace"
    )

    CURRENCY: str = Field(
        default="BDT"
    )

    DEFAULT_COMMISSION_PERCENT: float = Field(
        default=5.0
    )

    MIN_DEPOSIT: float = Field(
        default=50.0
    )

    MIN_WITHDRAW: float = Field(
        default=100.0
    )

    MAX_WITHDRAW: float = Field(
        default=25000.0
    )

    # ==========================
    # Wallet System
    # ==========================
    WALLET_ENABLED: bool = Field(default=True)
    BALANCE_TRANSFER_ENABLED: bool = Field(default=True)
    DEPOSIT_ENABLED: bool = Field(default=True)
    WITHDRAW_ENABLED: bool = Field(default=True)

    # ==========================
    # Payment Methods
    # ==========================
    PAYMENT_BKASH_ENABLED: bool = Field(default=True)
    PAYMENT_NAGAD_ENABLED: bool = Field(default=True)
    PAYMENT_ROCKET_ENABLED: bool = Field(default=False)

    PAYMENT_BINANCE_PAY_ENABLED: bool = Field(default=True)

    PAYMENT_USDT_TRC20_ENABLED: bool = Field(default=True)
    PAYMENT_USDT_BEP20_ENABLED: bool = Field(default=True)
    PAYMENT_USDT_SOLANA_ENABLED: bool = Field(default=False)

    # ==========================
    # Escrow
    # ==========================
    ESCROW_ENABLED: bool = Field(default=True)

    ESCROW_AUTO_RELEASE_HOURS: int = Field(
        default=24
    )

    ESCROW_DISPUTE_TIME_LIMIT_HOURS: int = Field(
        default=48
    )

    ESCROW_AUTO_CANCEL_HOURS: int = Field(
        default=12
    )

    # ==========================
    # Referral
    # ==========================
    REFERRAL_ENABLED: bool = Field(default=True)
    REFERRAL_BONUS_ENABLED: bool = Field(default=True)

    DEFAULT_REFERRAL_BONUS_AMOUNT: float = Field(
        default=10.0
    )

    # ==========================
    # Logging
    # ==========================
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE_NAME: str = Field(default="bot.log")

    CONSOLE_LOGGING: bool = Field(default=True)
    FILE_LOGGING: bool = Field(default=True)

    # ==========================
    # Environment
    # ==========================
    DEBUG: bool = Field(default=False)
    IS_PRODUCTION: bool = Field(default=True)


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Global Config Instance
Config = Config()
