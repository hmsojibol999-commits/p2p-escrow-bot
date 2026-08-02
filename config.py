import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Project Configuration Module using Pydantic Settings.
    Loads configurations from Render Environment Variables or .env file.
    Compatible with Python 3.12 & aiogram 3.x.
    """

    # ------------------------------------------------------------------
    # 1. ENVIRONMENT VARIABLES (Render Dashbaord matched)
    # ------------------------------------------------------------------
    BOT_TOKEN: str = Field(..., description="Telegram Bot API Token from @BotFather")
    BOT_USERNAME: str = Field(..., description="Bot Telegram Username without @")
    DATABASE_URL: str = Field(
        ..., description="PostgreSQL Database Connection URL"
    )
    DEBUG: bool = Field(False, description="Debug mode flag (True/False)")
    LOG_LEVEL: str = Field("INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")
    OWNER_ID: int = Field(..., description="Telegram User ID of the Main Owner")
    REQUIRED_CHANNEL: str = Field(
        "", description="Required Telegram Channel username or ID for force sub (e.g. @MyChannel)"
    )
    SECRET_KEY: str = Field(..., description="Secret key for security and hash verification")
    SUPPORT_ADMIN_ID: int = Field(..., description="Telegram User ID for Support Admin")

    # ------------------------------------------------------------------
    # 2. ROLE CONSTANTS
    # ------------------------------------------------------------------
    ROLE_OWNER: str = "OWNER"
    ROLE_SUPPORT_ADMIN: str = "SUPPORT_ADMIN"
    ROLE_USER: str = "USER"

    # ------------------------------------------------------------------
    # 3. DATABASE SETTINGS
    # ------------------------------------------------------------------
    DB_POOL_SIZE: int = Field(20, description="Database connection pool size")
    DB_POOL_TIMEOUT: int = Field(30, description="Database pool timeout in seconds")
    DB_AUTO_RECONNECT: bool = Field(True, description="Auto reconnect to DB on disconnect")
    DB_ECHO: bool = Field(False, description="SQLAlchemy Echo Mode for SQL query debugging")

    # ------------------------------------------------------------------
    # 4. BOT SETTINGS
    # ------------------------------------------------------------------
    PARSE_MODE: str = Field("HTML", description="Default parse mode for Telegram messages")
    DEFAULT_LANGUAGE: str = Field("bn", description="Default bot language")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default_factory=lambda: ["bn", "en"], description="List of supported language codes"
    )
    TIMEZONE: str = Field("Asia/Dhaka", description="Bot timezone")

    # ------------------------------------------------------------------
    # 5. MARKETPLACE SETTINGS
    # ------------------------------------------------------------------
    MARKETPLACE_NAME: str = Field("Digital Marketplace", description="Name of the Marketplace")
    CURRENCY: str = Field("BDT", description="Base currency code")
    DEFAULT_COMMISSION_PERCENT: float = Field(5.0, description="Default marketplace commission percentage")
    MIN_DEPOSIT: float = Field(50.0, description="Minimum allowed deposit amount")
    MIN_WITHDRAW: float = Field(100.0, description="Minimum allowed withdrawal amount")
    MAX_WITHDRAW: float = Field(25000.0, description="Maximum allowed withdrawal amount per request")
    MAX_PRODUCT_UPLOAD_SIZE_MB: int = Field(50, description="Max allowed file size for product uploads in MB")
    MAX_FILE_SIZE_MB: int = Field(100, description="General maximum file upload size in MB")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default_factory=lambda: ["zip", "rar", "txt", "pdf", "jpg", "png", "json"],
        description="Allowed file extensions for upload",
    )

    # ------------------------------------------------------------------
    # 6. WALLET SETTINGS
    # ------------------------------------------------------------------
    WALLET_ENABLED: bool = Field(True, description="Enable or disable wallet feature")
    BALANCE_TRANSFER_ENABLED: bool = Field(True, description="Enable or disable P2P balance transfer")
    DEPOSIT_ENABLED: bool = Field(True, description="Enable or disable deposit system")
    WITHDRAW_ENABLED: bool = Field(True, description="Enable or disable withdrawal system")

    # ------------------------------------------------------------------
    # 7. PAYMENT METHODS (FLAGS ONLY - NO WALLET ADDRESSES/NUMBERS)
    # ------------------------------------------------------------------
    PAYMENT_BKASH_ENABLED: bool = Field(True, description="Enable bKash payment gateway")
    PAYMENT_NAGAD_ENABLED: bool = Field(True, description="Enable Nagad payment gateway")
    PAYMENT_ROCKET_ENABLED: bool = Field(False, description="Enable Rocket payment gateway")
    PAYMENT_BINANCE_PAY_ENABLED: bool = Field(True, description="Enable Binance Pay gateway")
    PAYMENT_USDT_TRC20_ENABLED: bool = Field(True, description="Enable USDT (TRC20) payment gateway")
    PAYMENT_USDT_BEP20_ENABLED: bool = Field(True, description="Enable USDT (BEP20) payment gateway")
    PAYMENT_USDT_SOLANA_ENABLED: bool = Field(False, description="Enable USDT (Solana) payment gateway")

    # ------------------------------------------------------------------
    # 8. SECURITY SETTINGS
    # ------------------------------------------------------------------
    LOGIN_PIN_LENGTH: int = Field(4, description="Length of security PIN")
    MAX_WRONG_PIN_ATTEMPTS: int = Field(3, description="Max allowed wrong PIN attempts before locking")
    TEMPORARY_LOCK_TIME_MINUTES: int = Field(15, description="Lockout duration in minutes after failed attempts")
    SESSION_TIMEOUT_MINUTES: int = Field(60, description="User session timeout in minutes")
    RATE_LIMIT_MESSAGES_PER_SEC: float = Field(1.5, description="Anti-spam rate limit per user")
    MAX_LOGIN_ATTEMPTS: int = Field(5, description="Max total login attempts permitted")

    # ------------------------------------------------------------------
    # 9. ESCROW SETTINGS
    # ------------------------------------------------------------------
    ESCROW_ENABLED: bool = Field(True, description="Enable or disable escrow protection system")
    ESCROW_AUTO_RELEASE_HOURS: int = Field(24, description="Hours after which payment auto-releases to seller")
    ESCROW_DISPUTE_TIME_LIMIT_HOURS: int = Field(48, description="Time limit for buyers to open a dispute")
    ESCROW_AUTO_CANCEL_HOURS: int = Field(12, description="Hours after which an unpaid deal is auto-cancelled")

    # ------------------------------------------------------------------
    # 10. REFERRAL SETTINGS
    # ------------------------------------------------------------------
    REFERRAL_ENABLED: bool = Field(True, description="Enable or disable referral system")
    REFERRAL_BONUS_ENABLED: bool = Field(True, description="Enable or disable referral bonuses")
    DEFAULT_REFERRAL_BONUS_AMOUNT: float = Field(10.0, description="Default referral reward amount in BDT")

    # ------------------------------------------------------------------
    # 11. RATING SETTINGS
    # ------------------------------------------------------------------
    RATING_ENABLED: bool = Field(True, description="Enable or disable user rating/review system")
    MIN_RATING: int = Field(1, description="Minimum review rating star")
    MAX_RATING: int = Field(5, description="Maximum review rating star")

    # ------------------------------------------------------------------
    # 12. BUG REPORT SETTINGS
    # ------------------------------------------------------------------
    BUG_REPORT_ENABLED: bool = Field(True, description="Enable or disable user bug reporting feature")

    # ------------------------------------------------------------------
    # 13. LOGGING SETTINGS
    # ------------------------------------------------------------------
    LOG_FILE_NAME: str = Field("bot.log", description="Log file output destination name")
    CONSOLE_LOGGING: bool = Field(True, description="Enable console output logging")
    FILE_LOGGING: bool = Field(True, description="Enable writing logs to file")

    # ------------------------------------------------------------------
    # 14. RENDER & ENVIRONMENT SETTINGS
    # ------------------------------------------------------------------
    IS_PRODUCTION: bool = Field(True, description="Set True for production environment")

    # ------------------------------------------------------------------
    # CONFIGURATION SETTINGS (Pydantic V2)
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Global configuration instance
config = Settings()

    
