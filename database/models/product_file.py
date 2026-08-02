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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.product import Product
    from database.models.user import User


# ------------------------------------------------------------------
# ENUMS FOR STORAGE TYPES & FILE STATUS
# ------------------------------------------------------------------
class StorageType(str, enum.Enum):
    LOCAL = "LOCAL"
    CLOUD = "CLOUD"


class FileStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    DELETED = "DELETED"


class ProductFile(BaseModel):
    """
    Product File Storage Database Model.
    Stores file attachments and inventory data (TXT, CSV, XLSX, ZIP, etc.)
    for marketplace products, managing bulk item counts, secure downloads,
    access limits, and file integrity protection.
    """

    __tablename__ = "product_files"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    file_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique system-generated file identifier",
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        description="Foreign key referencing products table",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing seller's user ID",
    )

    # ------------------------------------------------------------------
    # 2. FILE METADATA & STORAGE LOCATION
    # ------------------------------------------------------------------
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="System-sanitized file name on server/cloud",
    )
    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Original name of file uploaded by seller",
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        description="File extension/type (e.g. TXT, CSV, XLSX, ZIP, PDF)",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        description="Size of the file in bytes",
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        description="Secure storage location reference or cloud object path",
    )
    storage_type: Mapped[StorageType] = mapped_column(
        SQLEnum(StorageType, name="storage_type_enum"),
        default=StorageType.LOCAL,
        nullable=False,
        description="Storage provider (LOCAL server storage or CLOUD)",
    )

    # ------------------------------------------------------------------
    # 3. BULK CONTENT & INVENTORY CONTROL
    # ------------------------------------------------------------------
    total_items: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        description="Total items/credentials contained within the file",
    )
    available_items: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        description="Remaining unsold items within the file",
    )
    sold_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Total items extracted and sold from this file",
    )

    # ------------------------------------------------------------------
    # 4. DOWNLOAD SECURITY & EXPIRY LIMITS
    # ------------------------------------------------------------------
    download_limit: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        description="Maximum allowed download count per purchase access",
    )
    access_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Optional timestamp when buyer download access expires",
    )
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        description="Flag indicating if the file content is encrypted on disk",
    )

    # ------------------------------------------------------------------
    # 5. FILE STATUS
    # ------------------------------------------------------------------
    status: Mapped[FileStatus] = mapped_column(
        SQLEnum(FileStatus, name="file_status_enum"),
        default=FileStatus.UPLOADED,
        index=True,
        nullable=False,
        description="Operational status of product file",
    )

    # ------------------------------------------------------------------
    # 6. RELATIONSHIPS
    # ------------------------------------------------------------------
    product: Mapped["Product"] = relationship("Product", backref="files")
    seller: Mapped["User"] = relationship("User", backref="uploaded_files")

    # ------------------------------------------------------------------
    # INDEXES FOR FAST ASSET RETRIEVAL
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_file_product_status", "product_id", "status"),
        Index("idx_file_seller_status", "seller_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProductFile(id={self.id}, file_id='{self.file_id}', "
            f"file_name='{self.file_name}', total_items={self.total_items}, "
            f"available_items={self.available_items}, status='{self.status.value}')>"
        )

