import enum
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric as SQLDecimal,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.category import Category
    from database.models.user import User


# ------------------------------------------------------------------
# ENUMS FOR PRODUCT TYPE, STATUS & DELIVERY MODE
# ------------------------------------------------------------------
class ProductType(str, enum.Enum):
    ACCOUNT = "ACCOUNT"
    FILE = "FILE"
    DIGITAL_PRODUCT = "DIGITAL_PRODUCT"
    SERVICE = "SERVICE"
    OTHER = "OTHER"


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SOLD_OUT = "SOLD_OUT"
    PENDING_REVIEW = "PENDING_REVIEW"
    BLOCKED = "BLOCKED"


class DeliveryMode(str, enum.Enum):
    INSTANT_DELIVERY = "INSTANT_DELIVERY"
    MANUAL_DELIVERY = "MANUAL_DELIVERY"
    ESCROW_REQUIRED = "ESCROW_REQUIRED"


class Product(BaseModel):
    """
    Marketplace Product Database Model.
    Core catalog entry created by sellers. Supports digital goods, files, accounts, and services.
    Includes stock management, delivery type classifications, pricing details, and moderation controls.
    """

    __tablename__ = "products"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    product_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system product identifier (e.g., PRD-XXXXXXXX)",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing seller user ID",
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing category primary key",
    )

    # ------------------------------------------------------------------
    # 2. PRODUCT BASIC INFORMATION
    # ------------------------------------------------------------------
    product_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
        description="Title or name of the product",
    )
    short_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        description="Brief highlights or preview description",
    )
    full_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Complete product specifications, requirements, and instructions",
    )
    product_type: Mapped[ProductType] = mapped_column(
        SQLEnum(ProductType, name="product_type_enum"),
        default=ProductType.DIGITAL_PRODUCT,
        nullable=False,
        description="Type category of item (ACCOUNT, FILE, DIGITAL_PRODUCT, SERVICE, OTHER)",
    )

    # ------------------------------------------------------------------
    # 3. PRICING SYSTEM & COMMISSION
    # ------------------------------------------------------------------
    price: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=18, scale=2),
        nullable=False,
        description="Unit listing price (Decimal strictly enforced)",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="BDT",
        nullable=False,
        description="Currency code for pricing (Default: BDT)",
    )
    commission_rate: Mapped[Decimal] = mapped_column(
        SQLDecimal(precision=5, scale=2),
        default=Decimal("0.00"),
        nullable=False,
        description="Percentage platform commission rate overrides for this product (e.g. 5.00 for 5%)",
    )

    # ------------------------------------------------------------------
    # 4. STOCK MANAGEMENT
    # ------------------------------------------------------------------
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Total original stock units added by seller",
    )
    sold_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Total units successfully purchased by buyers",
    )

    # ------------------------------------------------------------------
    # 5. STATUS & DELIVERY MODE
    # ------------------------------------------------------------------
    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, name="product_status_enum"),
        default=ProductStatus.PENDING_REVIEW,
        index=True,
        nullable=False,
        description="Moderation status (ACTIVE, INACTIVE, SOLD_OUT, PENDING_REVIEW, BLOCKED)",
    )
    delivery_mode: Mapped[DeliveryMode] = mapped_column(
        SQLEnum(DeliveryMode, name="delivery_mode_enum"),
        default=DeliveryMode.INSTANT_DELIVERY,
        nullable=False,
        description="How product payload is transferred (INSTANT_DELIVERY, MANUAL_DELIVERY, ESCROW_REQUIRED)",
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], backref="products"
    )
    category: Mapped["Category"] = relationship("Category", backref="products")

    # ------------------------------------------------------------------
    # HELPER PROPERTIES
    # ------------------------------------------------------------------
    @property
    def available_quantity(self) -> int:
        """Returns the currently available stock for sale."""
        return max(0, self.stock_quantity - self.sold_quantity)

    # ------------------------------------------------------------------
    # INDEXES FOR SEARCH & FILTER OPTIMIZATION
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_product_seller_status", "seller_id", "status"),
        Index("idx_product_category_status", "category_id", "status"),
        Index("idx_product_type_status", "product_type", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Product(id={self.id}, product_id='{self.product_id}', "
            f"name='{self.product_name}', price={self.price}, status='{self.status.value}')>"
  )
      
