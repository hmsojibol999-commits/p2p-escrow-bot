import enum
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
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
    from database.models.order import Order
    from database.models.product import Product
    from database.models.user import User


# ------------------------------------------------------------------
# ENUMS FOR DISPUTE STATUS & ADMIN DECISION
# ------------------------------------------------------------------
class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    WAITING_SELLER_RESPONSE = "WAITING_SELLER_RESPONSE"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED_BUYER = "RESOLVED_BUYER"
    RESOLVED_SELLER = "RESOLVED_SELLER"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class AdminDisputeDecision(str, enum.Enum):
    REFUND_BUYER = "REFUND_BUYER"
    RELEASE_SELLER_PAYMENT = "RELEASE_SELLER_PAYMENT"
    PARTIAL_REFUND = "PARTIAL_REFUND"
    NO_ACTION = "NO_ACTION"


class Dispute(BaseModel):
    """
    Buyer-Seller Dispute Database Model.
    Tracks complaint tickets, uploaded buyer/seller evidence, seller counter-responses,
    admin decisions, and resulting financial adjustments (refunds/penalties).
    """

    __tablename__ = "disputes"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    dispute_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated dispute identifier (e.g. DSP-XXXXXXXX)",
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
        description="Foreign key referencing main orders table primary key",
    )
    buyer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing complaining buyer user ID",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing defendant seller user ID",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing product table primary key",
    )

    # ------------------------------------------------------------------
    # 2. DISPUTE DETAILS
    # ------------------------------------------------------------------
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Categorized dispute reason (e.g., Product Not Working, Account Issue)",
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, description="Detailed explanation submitted by buyer"
    )

    # ------------------------------------------------------------------
    # 3. EVIDENCE ATTACHMENTS (Immutable References & Metadata)
    # ------------------------------------------------------------------
    screenshot: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, description="Screenshot proof URL or File ID"
    )
    video: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, description="Video proof URL or File ID"
    )
    additional_files: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        description="JSON payload containing extra files and upload timestamps",
    )

    # ------------------------------------------------------------------
    # 4. DISPUTE STATUS & SELLER RESPONSE
    # ------------------------------------------------------------------
    status: Mapped[DisputeStatus] = mapped_column(
        SQLEnum(DisputeStatus, name="dispute_status_enum"),
        default=DisputeStatus.OPEN,
        index=True,
        nullable=False,
        description="Current ticket state",
    )
    seller_response: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Counter-explanation provided by seller"
    )
    seller_replied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when seller submitted reply",
    )

    # ------------------------------------------------------------------
    # 5. ADMIN RESOLUTION & AUDIT
    # ------------------------------------------------------------------
    admin_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        description="Telegram Admin User ID who investigated and resolved dispute",
    )
    admin_decision: Mapped[Optional[AdminDisputeDecision]] = mapped_column(
        SQLEnum(AdminDisputeDecision, name="admin_dispute_decision_enum"),
        nullable=True,
        description="Final official verdict of Admin",
    )
    admin_note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Admin reasoning or investigation comments"
    )

    # ------------------------------------------------------------------
    # 6. FINANCIAL ACTIONS & ADJUSTMENTS
    # ------------------------------------------------------------------
    refund_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Amount refunded to buyer if dispute resolved in buyer's favor",
    )
    penalty_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Fine/Penalty amount deducted from violating party",
    )
    balance_adjusted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag indicating whether ledger balances were modified",
    )

    # ------------------------------------------------------------------
    # 7. RELATIONSHIPS
    # ------------------------------------------------------------------
    order: Mapped["Order"] = relationship("Order", backref="dispute", uselist=False)
    product: Mapped["Product"] = relationship("Product", backref="disputes")
    buyer: Mapped["User"] = relationship(
        "User", foreign_keys=[buyer_id], backref="disputes_as_buyer"
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], backref="disputes_as_seller"
    )

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_dispute_buyer_status", "buyer_id", "status"),
        Index("idx_dispute_seller_status", "seller_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Dispute(id={self.id}, dispute_id='{self.dispute_id}', "
            f"order_id={self.order_id}, buyer_id={self.buyer_id}, status='{self.status.value}')>"
        )

