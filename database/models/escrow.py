import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
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
    from database.models.order import Order
    from database.models.user import User


# ------------------------------------------------------------------
# ENUM FOR ESCROW STATUS
# ------------------------------------------------------------------
class EscrowState(str, enum.Enum):
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    HOLDING = "HOLDING"
    RELEASE_REQUESTED = "RELEASE_REQUESTED"
    RELEASED = "RELEASED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUNDED = "REFUNDED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class Escrow(BaseModel):
    """
    Escrow System Database Model.
    Holds buyer funds securely during high-value or sensitive marketplace trades.
    Manages fund releases to sellers, refunds to buyers, and admin dispute interventions.
    """

    __tablename__ = "escrows"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    escrow_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated escrow identifier (e.g., ESC-XXXXXXXX)",
    )
    buyer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing buyer user ID",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing seller user ID",
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
        description="Foreign key referencing the associated order",
    )

    # ------------------------------------------------------------------
    # 2. FINANCIAL INFORMATION (Precise Decimal Money Format)
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Gross escrow amount paid by buyer and held by platform",
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="BDT", nullable=False, description="Base currency code"
    )
    commission_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Platform fee to be deducted upon release",
    )
    seller_release_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Net payable amount to seller upon successful completion",
    )

    # ------------------------------------------------------------------
    # 3. ESCROW STATUS & TIMESTAMPS
    # ------------------------------------------------------------------
    status: Mapped[EscrowState] = mapped_column(
        SQLEnum(EscrowState, name="escrow_state_enum"),
        default=EscrowState.CREATED,
        index=True,
        nullable=False,
        description="Current state of held escrow funds",
    )
    funded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when buyer funds were locked in escrow",
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when funds were released to seller",
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when funds were refunded back to buyer",
    )

    # ------------------------------------------------------------------
    # 4. BUYER CONFIRMATION
    # ------------------------------------------------------------------
    buyer_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag indicating if buyer accepted product delivery",
    )
    confirmation_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Remarks or comments from buyer upon confirmation"
    )

    # ------------------------------------------------------------------
    # 5. DISPUTE SYSTEM INTEGRATION
    # ------------------------------------------------------------------
    dispute_opened: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag set to True if dispute is raised",
    )
    dispute_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Reason for opening dispute"
    )
    admin_decision: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Final decision and comments logged by Admin"
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    buyer: Mapped["User"] = relationship(
        "User", foreign_keys=[buyer_id], backref="escrows_as_buyer"
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], backref="escrows_as_seller"
    )
    order: Mapped["Order"] = relationship("Order", backref="escrow", uselist=False)

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_escrow_buyer_status", "buyer_id", "status"),
        Index("idx_escrow_seller_status", "seller_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Escrow(id={self.id}, escrow_id='{self.escrow_id}', buyer_id={self.buyer_id}, "
            f"seller_id={self.seller_id}, amount={self.amount}, status='{self.status.value}')>"
        )

