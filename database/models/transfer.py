import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
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
# ENUM FOR TRANSFER STATUS
# ------------------------------------------------------------------
class TransferStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Transfer(BaseModel):
    """
    User-to-User Balance Transfer Database Model.
    Tracks internal peer-to-peer (P2P) wallet fund transfers between marketplace users,
    including sender/receiver metrics, amounts, notes, status, and failure audit trails.
    
    Designed to be IMMUTABLE — transfer logs must never be deleted.
    """

    __tablename__ = "transfers"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    transfer_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system transfer identifier (e.g., TRF-XXXXXXXX)",
    )
    sender_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing sending user ID",
    )
    receiver_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing receiving user ID",
    )
    sender_wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing sending wallet ID",
    )
    receiver_wallet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("wallets.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing receiving wallet ID",
    )

    # ------------------------------------------------------------------
    # 2. TRANSFER FINANCIAL INFORMATION
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Monetary amount transferred (Decimal type strictly enforced)",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="BDT",
        nullable=False,
        description="Currency code for transfer (Default: BDT)",
    )
    transfer_note: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        description="Optional personal note or remark provided by sender",
    )

    # ------------------------------------------------------------------
    # 3. TRANSFER STATUS & AUDIT TRAIL
    # ------------------------------------------------------------------
    status: Mapped[TransferStatus] = mapped_column(
        SQLEnum(TransferStatus, name="transfer_status_enum"),
        default=TransferStatus.PENDING,
        index=True,
        nullable=False,
        description="Current status of the P2P transfer",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when funds were successfully moved",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Explanation if transfer failed (e.g., Insufficient Balance, Locked Receiver Wallet)",
    )

    # ------------------------------------------------------------------
    # 4. RELATIONSHIPS
    # ------------------------------------------------------------------
    sender_user: Mapped["User"] = relationship(
        "User", foreign_keys=[sender_user_id], backref="sent_transfers"
    )
    receiver_user: Mapped["User"] = relationship(
        "User", foreign_keys=[receiver_user_id], backref="received_transfers"
    )
    sender_wallet: Mapped["Wallet"] = relationship(
        "Wallet", foreign_keys=[sender_wallet_id], backref="outgoing_transfers"
    )
    receiver_wallet: Mapped["Wallet"] = relationship(
        "Wallet", foreign_keys=[receiver_wallet_id], backref="incoming_transfers"
    )

    # ------------------------------------------------------------------
    # CONSTRAINTS & INDEXES FOR SECURITY & PERFORMANCE
    # ------------------------------------------------------------------
    __table_args__ = (
        # Ensure sender and receiver are not the same user
        CheckConstraint(
            "sender_user_id <> receiver_user_id", name="ck_prevent_self_transfer"
        ),
        Index("idx_transfer_sender_status", "sender_user_id", "status"),
        Index("idx_transfer_receiver_status", "receiver_user_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transfer(id={self.id}, transfer_id='{self.transfer_id}', "
            f"sender={self.sender_user_id}, receiver={self.receiver_user_id}, "
            f"amount={self.amount}, status='{self.status.value}')>"
        )
      
