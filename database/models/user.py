
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, Float, Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel


class User(BaseModel):
    """
    User Database Model.
    Represents Telegram users and stores account security, wallet balances,
    seller statistics, referral information, and activity data.
    """

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # 1. BASIC TELEGRAM INFORMATION
    # ------------------------------------------------------------------
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False, description="Telegram User ID"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, description="Telegram Username"
    )
    first_name: Mapped[str] = mapped_column(
        String(255), nullable=False, description="User First Name"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, description="User Last Name"
    )

    # ------------------------------------------------------------------
    # 2. ACCOUNT SECURITY FIELDS
    # ------------------------------------------------------------------
    pin_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, description="Hashed 4-digit security PIN"
    )
    pin_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, description="Failed PIN attempt counter"
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, description="Account temporary lock status"
    )
    lock_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, description="Lock expiry timestamp"
    )

    # ------------------------------------------------------------------
    # 3. ACCOUNT STATUS
    # ------------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, description="User active status"
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, description="User ban status"
    )
    ban_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Reason for ban if applicable"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, description="KYC/User verification status"
    )

    # ------------------------------------------------------------------
    # 4. WALLET RELATED FIELDS
    # ------------------------------------------------------------------
    balance: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Available balance in BDT"
    )
    held_balance: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Escrow or pending locked balance"
    )
    total_deposit: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Total deposit sum"
    )
    total_withdraw: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Total withdrawal sum"
    )
    total_spent: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Total spent on purchases"
    )
    total_earned: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Total earned as seller"
    )

    # ------------------------------------------------------------------
    # 5. SELLER SYSTEM FIELDS
    # ------------------------------------------------------------------
    is_seller: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, description="Seller mode flag"
    )
    seller_rating: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Average seller rating"
    )
    total_sales: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, description="Total completed sales count"
    )
    commission_paid: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Total platform commission paid"
    )

    # ------------------------------------------------------------------
    # 6. REFERRAL SYSTEM FIELDS
    # ------------------------------------------------------------------
    referral_code: Mapped[Optional[str]] = mapped_column(
        String(64), unique=True, index=True, nullable=True, description="Unique referral code"
    )
    referred_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, description="Telegram ID of the referrer"
    )
    total_referrals: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, description="Total successfully referred users"
    )
    referral_bonus: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, description="Total earned referral bonus"
    )

    # ------------------------------------------------------------------
    # 7. SUPPORT / ACTIVITY FIELDS
    # ------------------------------------------------------------------
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, description="Last bot interaction timestamp"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, description="Last login timestamp"
    )
    language: Mapped[str] = mapped_column(
        String(10), default="bn", nullable=False, description="Preferred language code"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"
  
