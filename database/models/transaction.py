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
    SALE_PAYMENT = "SALE_PAYMENT"
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
    REFUNDED = "REFUNDED"


class CreatedByType(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"


class Transaction(BaseModel):
    """
    Financial Transaction Ledger Core Model.
    Records every single monetary event across the marketplace (Deposits, Withdrawals,
    P2P Transfers, Purchases, Escrow Operations, Commission, and Admin Adjustments).
    
    Designed to be IMMUTABLE — records must never be deleted or altered directly.
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
        description="Unique system-generated transaction identifier (e.g. TXN-XXXXXXXX)",
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
    # 2. TRANSACTION TYPE & STATUS
    # ------------------------------------------------------------------
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type_enum"),
        index=True,
        nullable=False,
        description="Categorization of the ledger entry",
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus, name="transaction_status_enum"),
        default=TransactionStatus.PENDING,
        index=True,
        nullable=False,
        description="Current state of the transaction lifecycle",
    )

    # ------------------------------------------------------------------
    # 3. AMOUNT INFORMATION (Precise Financial Decimal)
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Gross monetary value of the transaction (Decimal strictly enforced)",
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
        String(10),
        default="BDT",
        nullable=False,
        description="Currency code associated with the entry",
    )

    # ------------------------------------------------------------------
    # 4. PAYMENT GATEWAY & EXTERNAL DATA
    # ------------------------------------------------------------------
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        description="Payment method used (e.g. bKash, Nagad, Binance, USDT)",
    )
    external_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        index=True,
        nullable=True,
        description="External gateway Transaction ID or Blockchain Hash",
    )

    # ------------------------------------------------------------------
    # 5. DESCRIPTION, AUDIT TRAILS & NOTES
    # ------------------------------------------------------------------
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Human-readable ledger remark or automated system narration",
    )
    admin_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Admin justification or audit logs in case of manual adjustment",
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
        String(45),
        nullable=True,
        description="IP address for security audit",
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
    # INDEXES FOR OPTIMIZED QUERYING & REPORTING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_type_status", "transaction_type", "status"),
        Index("idx_txn_user_type_status", "user_id", "transaction_type", "status"),
        Index("idx_txn_wallet_created", "wallet_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, transaction_id='{self.transaction_id}', "
            f"user_id={self.user_id}, type='{self.transaction_type.value}', "
            f"amount={self.amount}, status='{self.status.value}')>"
        )
        
