import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.order import Order
    from database.models.product import Product
    from database.models.product_file import ProductFile
    from database.models.user import User


# ------------------------------------------------------------------
# ENUMS FOR DELIVERY TYPE & DELIVERY STATUS
# ------------------------------------------------------------------
class DeliveryContentType(str, enum.Enum):
    FILE = "FILE"
    TEXT = "TEXT"
    ACCOUNT = "ACCOUNT"
    MANUAL = "MANUAL"


class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Delivery(BaseModel):
    """
    Product Delivery Database Model.
    Tracks delivered digital assets (Files, Text credentials, License keys),
    buyer access/download logs, receipt confirmation timestamps, and dispute audit trails.
    """

    __tablename__ = "deliveries"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    delivery_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated delivery identifier (e.g. DEL-XXXXXXXX)",
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
        description="Foreign key referencing buyer user ID",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing seller user ID",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing product table primary key",
    )

    # ------------------------------------------------------------------
    # 2. DELIVERY TYPE & CONTENT REFERENCES
    # ------------------------------------------------------------------
    delivery_type: Mapped[DeliveryContentType] = mapped_column(
        SQLEnum(DeliveryContentType, name="delivery_content_type_enum"),
        nullable=False,
        description="Type of delivered content (FILE, TEXT, ACCOUNT, MANUAL)",
    )
    file_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("product_files.id", ondelete="SET NULL"),
        nullable=True,
        description="Foreign key to product_files table if File delivery",
    )
    delivery_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Encrypted/Text payload (Credentials, License Keys, Access Info)",
    )

    # ------------------------------------------------------------------
    # 3. DELIVERY STATUS & CONFIRMATION
    # ------------------------------------------------------------------
    status: Mapped[DeliveryStatus] = mapped_column(
        SQLEnum(DeliveryStatus, name="delivery_status_enum"),
        default=DeliveryStatus.PENDING,
        index=True,
        nullable=False,
        description="Operational delivery state",
    )
    buyer_received: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag indicating if buyer acknowledged delivery receipt",
    )
    buyer_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when buyer confirmed product receipt",
    )

    # ------------------------------------------------------------------
    # 4. ACCESS TRACKING & AUDIT METRICS
    # ------------------------------------------------------------------
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Number of times buyer viewed sensitive content",
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Number of times buyer downloaded the asset file",
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp of buyer's most recent access/download",
    )

    # ------------------------------------------------------------------
    # 5. RELATIONSHIPS
    # ------------------------------------------------------------------
    order: Mapped["Order"] = relationship("Order", backref="delivery", uselist=False)
    product: Mapped["Product"] = relationship("Product", backref="deliveries")
    product_file: Mapped[Optional["ProductFile"]] = relationship(
        "ProductFile", backref="deliveries"
    )
    buyer: Mapped["User"] = relationship(
        "User", foreign_keys=[buyer_id], backref="received_deliveries"
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], backref="sent_deliveries"
    )

    # ------------------------------------------------------------------
    # INDEXES FOR FAST AUDIT & QUERY OPTIMIZATION
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_delivery_buyer_status", "buyer_id", "status"),
        Index("idx_delivery_seller_status", "seller_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Delivery(id={self.id}, delivery_id='{self.delivery_id}', "
            f"order_id={self.order_id}, buyer_id={self.buyer_id}, "
            f"type='{self.delivery_type.value}', status='{self.status.value}')>"
        )

