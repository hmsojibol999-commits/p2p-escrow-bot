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
    Integer,
    Numeric as SQLDecimal,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.order import Order
    from database.models.product import Product


# ------------------------------------------------------------------
# ENUM FOR ITEM DELIVERY TYPES
# ------------------------------------------------------------------
class ItemDeliveryType(str, enum.Enum):
    INSTANT = "INSTANT"
    MANUAL = "MANUAL"
    ESCROW = "ESCROW"


class OrderItem(BaseModel):
    """
    Order Item Database Model.
    Stores granular product snapshots per order line item.
    Enables future bulk checkout, multi-item baskets, and precise delivery tracking.
    """

    __tablename__ = "order_items"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        description="Foreign key referencing main orders table primary key",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing products table primary key",
    )

    # ------------------------------------------------------------------
    # 2. PRODUCT SNAPSHOT AT PURCHASE TIME
    # ------------------------------------------------------------------
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Snapshot of product title at time of purchase",
    )
    product_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        description="Snapshot of product category at time of purchase",
    )
    product_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        description="Snapshot of product classification (FILE, TEXT, ACCOUNT, SERVICE)",
    )

    # ------------------------------------------------------------------
    # 3. QUANTITY & PRICING BREAKDOWN (Decimal Money Format)
    # ------------------------------------------------------------------
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        description="Quantity of units purchased in this order line",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Price per single unit at purchase time",
    )
    total_price: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Calculated line item total (quantity * unit_price)",
    )

    # ------------------------------------------------------------------
    # 4. DELIVERY & ACCESS SYSTEM
    # ------------------------------------------------------------------
    delivery_type: Mapped[ItemDeliveryType] = mapped_column(
        SQLEnum(ItemDeliveryType, name="item_delivery_type_enum"),
        default=ItemDeliveryType.INSTANT,
        nullable=False,
        description="Fulfillment mode for this item",
    )
    delivery_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag indicating if digital asset delivery succeeded",
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when digital asset was delivered to buyer",
    )

    # ------------------------------------------------------------------
    # 5. FILE & ASSET DELIVERY REFERENCE
    # ------------------------------------------------------------------
    delivery_file_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        description="Reference or Telegram File ID / path delivered to buyer",
    )
    access_granted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag indicating if buyer has accessed/downloaded content",
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    order: Mapped["Order"] = relationship("Order", backref="items")
    product: Mapped["Product"] = relationship("Product", backref="order_items")

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_order_item_order_prod", "order_id", "product_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, "
            f"quantity={self.quantity}, total_price={self.total_price})>"
        )

