
import enum
from decimal import Decimal
from typing import Any, Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    JSON,
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
# ENUMS FOR TRANSACTION TYPES, STATUS, AND CREATED_BY
# ------------------------------------------------------------------
class TransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER_SEND = "TRANSFER_SEND"
    TRANSFER_RECEIVE = "TRANSFER_RECEIVE"
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    COMMISSION = "COMMISSION"
    REFUND = "REFUND"
    ESCROW_HOLD = "ESCROW_HOLD"
    ESCROW_RELEASE = "ESCROW_RELEASE"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"
    BONUS = "BONUS"
    PENALTY = "PENALTY"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class CreatedByType(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"


class Transaction(BaseModel):
    """
    Transaction Database Model.
    Records all monetary movements (Deposits, Withdrawals, Escrows, Purchases, Admin Adjustments).
    Financial history is immutable to prevent corruption or silent deletion.
    """

    __tablename__ = "transactions"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    transaction_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated transaction identifier",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key to users table",
    )
    wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key to wallets table",
    )

    # ------------------------------------------------------------------
    # 2. TRANSACTION TYPE & STATUS
    # ------------------------------------------------------------------
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type_enum"),
        index=True,
        nullable=False,
        description="Type of financial transaction",
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus, name="transaction_status_enum"),
        default=TransactionStatus.PENDING,
        index=True,
        nullable=False,
        description="Current transaction processing state",
    )

    # ------------------------------------------------------------------
    # 3. AMOUNT INFORMATION (Precise Financial Decimal)
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Gross transaction amount",
    )
    fee: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Service/Gateway processing fee charged",
    )
    net_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Net amount after fee calculation",
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="BDT", nullable=False, description="Currency code"
    )

    # ------------------------------------------------------------------
    # 4. PAYMENT GATEWAY / EXTERNAL DATA
    # ------------------------------------------------------------------
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        description="Payment method used (e.g. bKash, Nagad, Binance, USDT)",
    )
    external_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        description="External gateway Transaction ID or Blockchain Hash",
    )

    # ------------------------------------------------------------------
    # 5. DESCRIPTION & AUDIT TRAILS
    # ------------------------------------------------------------------
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Human-readable description or remarks"
    )
    created_by: Mapped[CreatedByType] = mapped_column(
        SQLEnum(CreatedByType, name="created_by_enum"),
        default=CreatedByType.SYSTEM,
        nullable=False,
        description="Entity that initiated the transaction",
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        description="Telegram Admin User ID who approved/handled this transaction",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, description="IP address for security audit"
    )
    metadata_info: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        description="Additional flexible metadata payload in JSON format",
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", backref="transactions")
    wallet: Mapped["Wallet"] = relationship("Wallet", backref="transactions")

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_type_status", "transaction_type", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, tx_id='{self.transaction_id}', "
            f"type='{self.transaction_type.value}', amount={self.amount}, status='{self.status.value}')>"
  )
      
