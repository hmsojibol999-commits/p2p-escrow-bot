import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric as SQLDecimal,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.user import User
    from database.models.wallet import Wallet


# ------------------------------------------------------------------
# ENUMS FOR WITHDRAW METHODS, BINANCE TYPES & STATUS
# ------------------------------------------------------------------
class WithdrawMethodType(str, enum.Enum):
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    ROCKET = "ROCKET"
    BINANCE = "BINANCE"
    USDT = "USDT"


class BinanceTargetType(str, enum.Enum):
    BINANCE_UID = "BINANCE_UID"
    PAY_ID = "PAY_ID"
    WALLET_ADDRESS = "WALLET_ADDRESS"


class WithdrawStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Withdraw(BaseModel):
    """
    Withdraw Request Database Model.
    Manages user withdrawal requests, gateway payout details, fee breakdowns,
    crypto network specifications, masked account displays, and admin logs.
    """

    __tablename__ = "withdraws"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    withdraw_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system withdrawal identifier (e.g., WTH-XXXXXXXX)",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing users table primary key",
    )
    wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing wallets table primary key",
    )

    # ------------------------------------------------------------------
    # 2. AMOUNT INFORMATION (Precise Decimal)
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Requested withdrawal gross monetary amount",
    )
    fee: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Withdrawal service/gateway fee charged",
    )
    net_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Net payout amount to user after fee deduction",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="BDT",
        nullable=False,
        description="Currency code for withdrawal (Default: BDT)",
    )

    # ------------------------------------------------------------------
    # 3. WITHDRAW METHOD & RECEIVER INFO
    # ------------------------------------------------------------------
    withdraw_method: Mapped[WithdrawMethodType] = mapped_column(
        SQLEnum(WithdrawMethodType, name="withdraw_method_enum"),
        index=True,
        nullable=False,
        description="Payout method selected by user (BKASH, NAGAD, ROCKET, BINANCE, USDT)",
    )
    receiver_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        description="Optional account holder name",
    )
    receiver_account: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Full destination phone number, Binance UID, or Crypto Wallet Address",
    )
    masked_receiver_account: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        description="Masked receiver account for safe user display (e.g., 018****5678)",
    )

    # ------------------------------------------------------------------
    # 4. BINANCE & CRYPTO NETWORK SPECIFIC FIELDS
    # ------------------------------------------------------------------
    binance_type: Mapped[Optional[BinanceTargetType]] = mapped_column(
        SQLEnum(BinanceTargetType, name="binance_type_enum"),
        nullable=True,
        description="Binance identification type (UID, Pay ID, or Address)",
    )
    network: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        description="Crypto network protocol (e.g., TRC20, BEP20, SOLANA)",
    )

    # ------------------------------------------------------------------
    # 5. WITHDRAW STATUS & ADMIN PROCESSING
    # ------------------------------------------------------------------
    status: Mapped[WithdrawStatus] = mapped_column(
        SQLEnum(WithdrawStatus, name="withdraw_status_enum"),
        default=WithdrawStatus.PENDING,
        index=True,
        nullable=False,
        description="Current payout status of the withdrawal request",
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        description="Telegram Admin User ID who processed, approved, or rejected this request",
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when withdrawal was completed, rejected, or cancelled",
    )
    admin_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Admin explanation, payout proof/TX hash note, or rejection reason",
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", backref="withdraws")
    wallet: Mapped["Wallet"] = relationship("Wallet", backref="withdraws")

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED AUDIT & LOOKUP
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_withdraw_user_status", "user_id", "status"),
        Index("idx_withdraw_method_status", "withdraw_method", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Withdraw(id={self.id}, withdraw_id='{self.withdraw_id}', "
            f"user_id={self.user_id}, net_amount={self.net_amount}, status='{self.status.value}')>"
        )
        
