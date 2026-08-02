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
    from database.models.product import Product
    from database.models.user import User


# ------------------------------------------------------------------
# ENUMS FOR ORDER STATUS, DELIVERY STATUS & ESCROW STATUS
# ------------------------------------------------------------------
class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class DeliveryStatus(str, enum.Enum):
    NOT_DELIVERED = "NOT_DELIVERED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class EscrowStatus(str, enum.Enum):
    HOLD = "HOLD"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


class Order(BaseModel):
    """
    Marketplace Order Database Model.
    Records buyer purchase history, seller commissions, delivery status,
    escrow holds, confirmation timestamps, and dispute parameters.
    """

    __tablename__ = "orders"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    order_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated order ID (e.g. ORD-XXXXXXXX)",
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

    # ------------------------------------------------------------------
    # 2. PRODUCT INFORMATION & SNAPSHOT
    # ------------------------------------------------------------------
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing products table",
    )
    product_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Snapshot of product title at time of purchase",
    )

    # ------------------------------------------------------------------
    # 3. FINANCIAL BREAKDOWN (Precise Decimal Money Format)
    # ------------------------------------------------------------------
    product_price: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Gross purchase price of the product",
    )
    commission_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Platform fee deducted from the sale",
    )
    seller_amount: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Net payable amount to seller after commission deduction",
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="BDT", nullable=False, description="Currency code"
    )

    # ------------------------------------------------------------------
    # 4. ORDER & DELIVERY STATUS
    # ------------------------------------------------------------------
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.CREATED,
        index=True,
        nullable=False,
        description="Overall lifecycle state of the order",
    )
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus, name="delivery_status_enum"),
        default=DeliveryStatus.NOT_DELIVERED,
        nullable=False,
        description="Product fulfillment / delivery status",
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when digital product/credential was delivered",
    )

    # ------------------------------------------------------------------
    # 5. ESCROW PROTECTION FIELDS
    # ------------------------------------------------------------------
    is_escrow: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        description="Flag indicating if escrow protection is enabled",
    )
    escrow_status: Mapped[Optional[EscrowStatus]] = mapped_column(
        SQLEnum(EscrowStatus, name="escrow_status_enum"),
        default=EscrowStatus.HOLD,
        nullable=True,
        description="Escrow fund hold state",
    )

    # ------------------------------------------------------------------
    # 6. BUYER CONFIRMATION
    # ------------------------------------------------------------------
    buyer_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Buyer manually confirmed product receipt",
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when buyer confirmed completion",
    )

    # ------------------------------------------------------------------
    # 7. DISPUTE & AUDIT MANAGEMENT
    # ------------------------------------------------------------------
    has_issue: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag set to True if buyer opens a dispute/ticket",
    )
    dispute_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Reason provided by buyer for dispute"
    )
    admin_decision: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Remarks and final resolution notes from Admin"
    )

    # ------------------------------------------------------------------
    # 8. RELATIONSHIPS
    # ------------------------------------------------------------------
    buyer: Mapped["User"] = relationship(
        "User", foreign_keys=[buyer_id], backref="bought_orders"
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], backref="sold_orders"
    )
    product: Mapped["Product"] = relationship("Product", backref="orders")

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_order_buyer_status", "buyer_id", "status"),
        Index("idx_order_seller_status", "seller_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, order_id='{self.order_id}', buyer_id={self.buyer_id}, "
            f"seller_id={self.seller_id}, price={self.product_price}, status='{self.status.value}')>"
        )
      
