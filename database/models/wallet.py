
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


# ------------------------------------------------------------------
# ENUM FOR WALLET STATUS
# ------------------------------------------------------------------
class WalletStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"


class Wallet(BaseModel):
    """
    Final User Wallet Database Model (Core Financial Engine).
    Stores real-time available liquid balances, locked/held funds (escrow, pending withdraws),
    comprehensive lifetime metrics (deposited, withdrawn, spent, received, sent),
    and security status controls.
    """

    __tablename__ = "wallets"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    wallet_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system wallet identifier (e.g., WAL-XXXXXXXX)",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
        description="Foreign key referencing users table primary key",
    )

    # ------------------------------------------------------------------
    # 2. BALANCE & HOLD SYSTEM (Precise Decimal - Never Float)
    # ------------------------------------------------------------------
    balance: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Liquid available balance for purchases, transfers, or withdrawals",
    )
    hold_balance: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Funds locked in active Escrow, pending Withdrawals, or Disputes",
    )

    # ------------------------------------------------------------------
    # 3. COMPREHENSIVE LIFETIME METRICS
    # ------------------------------------------------------------------
    total_deposited: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Lifetime aggregate amount deposited into this wallet",
    )
    total_withdrawn: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Lifetime aggregate amount successfully withdrawn",
    )
    total_purchase: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Lifetime aggregate amount spent on marketplace purchases",
    )
    total_received: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Lifetime aggregate amount received via P2P transfers or sales",
    )
    total_sent: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Lifetime aggregate amount sent via user-to-user transfers",
    )

    # ------------------------------------------------------------------
    # 4. CURRENCY & WALLET SECURITY STATUS
    # ------------------------------------------------------------------
    currency: Mapped[str] = mapped_column(
        String(10),
        default="BDT",
        nullable=False,
        description="Base wallet currency code (Default: BDT, Future: USDT, USD)",
    )
    status: Mapped[WalletStatus] = mapped_column(
        SQLEnum(WalletStatus, name="wallet_status_enum"),
        default=WalletStatus.ACTIVE,
        index=True,
        nullable=False,
        description="Operational status of wallet (ACTIVE, LOCKED, SUSPENDED)",
    )
    lock_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Admin explanation or automated system note if wallet is locked/suspended",
    )

    # ------------------------------------------------------------------
    # 5. AUDIT & LAST TRANSACTION REFERENCE
    # ------------------------------------------------------------------
    last_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        description="Reference identifier of the most recent financial transaction",
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", backref="wallet", uselist=False)

    # ------------------------------------------------------------------
    # HELPER COMPUTED PROPERTIES
    # ------------------------------------------------------------------
    @property
    def total_balance(self) -> Decimal:
        """Returns aggregate total balance (Available + Held funds)."""
        return self.balance + self.hold_balance

    @property
    def is_active(self) -> bool:
        """Checks if the wallet is in active status."""
        return self.status == WalletStatus.ACTIVE

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_wallet_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Wallet(id={self.id}, wallet_id='{self.wallet_id}', user_id={self.user_id}, "
            f"balance={self.balance}, hold={self.hold_balance}, status='{self.status.value}')>"
  )
      
