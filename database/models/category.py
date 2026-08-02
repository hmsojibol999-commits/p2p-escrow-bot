import enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
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
    from database.models.product import Product


# ------------------------------------------------------------------
# ENUM FOR CATEGORY TYPES
# ------------------------------------------------------------------
class CategoryType(str, enum.Enum):
    ACCOUNT = "ACCOUNT"
    FILE = "FILE"
    SERVICE = "SERVICE"
    DIGITAL_PRODUCT = "DIGITAL_PRODUCT"
    OTHER = "OTHER"


class Category(BaseModel):
    """
    Marketplace Category & Subcategory Database Model.
    Supports hierarchical categories (Main Category and Subcategories via Self-Relationship),
    icons, sorting priority, and active state visibility filters.
    """

    __tablename__ = "categories"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & PARENT-CHILD (SELF) RELATIONSHIP
    # ------------------------------------------------------------------
    category_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated category identifier",
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        description="Parent Category ID for subcategories (Self Reference)",
    )

    # ------------------------------------------------------------------
    # 2. CATEGORY INFORMATION
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False, description="Category name (e.g., Email, VPN)"
    )
    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
        description="URL/Search friendly identifier slug",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Detailed category explanation or rules"
    )

    # ------------------------------------------------------------------
    # 3. DISPLAY & SORTING CONTROL
    # ------------------------------------------------------------------
    icon: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, description="Emoji or Icon reference"
    )
    image: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, description="Image URL/Path for Web/Mini App support"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, description="Priority display position"
    )

    # ------------------------------------------------------------------
    # 4. STATUS & CATEGORY TYPE
    # ------------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, description="Active status for marketplace visibility"
    )
    category_type: Mapped[CategoryType] = mapped_column(
        SQLEnum(CategoryType, name="category_type_enum"),
        default=CategoryType.DIGITAL_PRODUCT,
        nullable=False,
        description="Classification of category",
    )

    # ------------------------------------------------------------------
    # 5. SELF-REFERENCING RELATIONSHIPS & PRODUCT BACKREF
    # ------------------------------------------------------------------
    # Subcategories under this category
    subcategories: Mapped[List["Category"]] = relationship(
        "Category",
        backref=relationship("Category", remote_side="Category.id"),
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED MARKETPLACE QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_category_active_parent", "is_active", "parent_id"),
        Index("idx_category_active_type", "is_active", "category_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}', "
            f"parent_id={self.parent_id}, is_active={self.is_active})>"
        )

