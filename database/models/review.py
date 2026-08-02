import enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.order import Order
    from database.models.product import Product
    from database.models.user import User


# ------------------------------------------------------------------
# ENUM FOR REVIEW MODERATION STATUS
# ------------------------------------------------------------------
class ReviewStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    HIDDEN = "HIDDEN"
    REMOVED = "REMOVED"


class Review(BaseModel):
    """
    Product Review & Rating Database Model.
    Tracks buyer ratings (1 to 5 stars), written reviews, verified purchase status,
    helpful counts, abuse reports, and seller reputation metrics.
    """

    __tablename__ = "reviews"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    review_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated review identifier",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing reviewer buyer user ID",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing product seller user ID",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing product table primary key",
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("orders.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
        description="Foreign key referencing verified purchase order primary key",
    )

    # ------------------------------------------------------------------
    # 2. RATING & REVIEW CONTENT
    # ------------------------------------------------------------------
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        description="Star rating given by buyer (1 to 5 stars)",
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True, description="Short summary headline of review"
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Detailed user feedback or experience text"
    )

    # ------------------------------------------------------------------
    # 3. VERIFICATION & STATUS CONTROL
    # ------------------------------------------------------------------
    is_verified_purchase: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        description="Flag denoting review originates from a completed real order",
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status_enum"),
        default=ReviewStatus.ACTIVE,
        index=True,
        nullable=False,
        description="Moderation status of review (ACTIVE, PENDING, HIDDEN, REMOVED)",
    )

    # ------------------------------------------------------------------
    # 4. HELPFULNESS & COMMUNITY REPORT SYSTEM
    # ------------------------------------------------------------------
    helpful_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Number of users who marked this review as helpful",
    )
    report_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Number of abuse/spam flags reported against this review",
    )

    # ------------------------------------------------------------------
    # 5. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], backref="submitted_reviews"
    )
    seller: Mapped["User"] = relationship(
        "User", foreign_keys=[seller_id], backref="received_reviews"
    )
    product: Mapped["Product"] = relationship("Product", backref="reviews")
    order: Mapped["Order"] = relationship("Order", backref="review", uselist=False)

    # ------------------------------------------------------------------
    # CONSTRAINTS & INDEXES FOR SECURITY & OPTIMIZATION
    # ------------------------------------------------------------------
    __table_args__ = (
        # Ensure a buyer can leave at most one review per order
        UniqueConstraint("order_id", name="uq_review_order_id"),
        Index("idx_review_product_status", "product_id", "status"),
        Index("idx_review_seller_status", "seller_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Review(id={self.id}, review_id='{self.review_id}', "
            f"user_id={self.user_id}, rating={self.rating}, status='{self.status.value}')>"
  )
      
