
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
# ENUMS FOR DEPOSIT PAYMENT METHODS, PROOF STATUS & DEPOSIT STATUS
# ------------------------------------------------------------------
class PaymentMethodType(str, enum.Enum):
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    ROCKET = "ROCKET"
    BINANCE = "BINANCE"
    USDT = "USDT"


class ProofStatus(str, enum.Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class DepositStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Deposit(BaseModel):
    """
    Deposit Request Database Model.
    Tracks user deposit requests, payment methods, transaction references,
    screenshot proofs, and admin approval workflows.
    """

    __tablename__ = "deposits"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    deposit_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated deposit request identifier",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing users table",
    )

    # ------------------------------------------------------------------
    # 2. DEPOSIT AMOUNT & CURRENCY
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Requested deposit amount in Decimal format",
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="BDT", nullable=False, description="Currency code"
    )

    # ------------------------------------------------------------------
    # 3. PAYMENT METHOD & SENDER INFO
    # ------------------------------------------------------------------
    payment_method: Mapped[PaymentMethodType] = mapped_column(
        SQLEnum(PaymentMethodType, name="payment_method_enum"),
        index=True,
        nullable=False,
        description="Payment gateway method used",
    )
    sender_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        description="Sender phone number, wallet address or Binance ID",
    )

    # ------------------------------------------------------------------
    # 4. TRANSACTION VERIFICATION & PROOF
    # ------------------------------------------------------------------
    transaction_reference: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
        description="Unique external gateway transaction ID (e.g. TrxID / Hash)",
    )
    payment_screenshot: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        description="File ID or URL path of payment screenshot proof",
    )
    proof_status: Mapped[ProofStatus] = mapped_column(
        SQLEnum(ProofStatus, name="proof_status_enum"),
        default=ProofStatus.NOT_SUBMITTED,
        nullable=False,
        description="Screenshot/Proof verification state",
    )

    # ------------------------------------------------------------------
    # 5. DEPOSIT STATUS & ADMIN PROCESSING
    # ------------------------------------------------------------------
    status: Mapped[DepositStatus] = mapped_column(
        SQLEnum(DepositStatus, name="deposit_status_enum"),
        default=DepositStatus.PENDING,
        index=True,
        nullable=False,
        description="Overall approval status of deposit request",
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        description="Telegram ID of the admin who processed this deposit",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when deposit was approved/rejected",
    )
    admin_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Remarks or rejection reason from Admin"
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", backref="deposits")

    # ------------------------------------------------------------------
    # HELPER METHOD TO MASK SENDER NUMBER FOR SECURITY
    # ------------------------------------------------------------------
    @property
    def masked_sender_number(self) -> str:
        """Returns masked sender phone number for safe display (e.g., 01******789)."""
        if not self.sender_number:
            return "N/A"
        if len(self.sender_number) >= 11:
            return f"{self.sender_number[:2]}******{self.sender_number[-3:]}"
        return self.sender_number

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_deposit_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Deposit(id={self.id}, deposit_id='{self.deposit_id}', "
            f"user_id={self.user_id}, amount={self.amount}, status='{self.status.value}')>"
        )
      
