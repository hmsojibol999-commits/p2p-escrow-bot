from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Enum,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.models.base import (
    Base,
    IDMixin,
    TimestampMixin,
)

import enum



class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SOLD_OUT = "SOLD_OUT"
    BLOCKED = "BLOCKED"



class DeliveryMode(str, enum.Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"



class Product(
    Base,
    IDMixin,
    TimestampMixin
):
    """
    Marketplace Product Model.
    Handles digital products, stock and seller information.
    """


    __tablename__ = "products"


    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )


    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )


    price: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    commission_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5,2),
        nullable=True,
    )


    available_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )


    sold_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )


    delivery_mode: Mapped[DeliveryMode] = mapped_column(
        Enum(DeliveryMode),
        default=DeliveryMode.AUTO,
        nullable=False,
    )


    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus),
        default=ProductStatus.ACTIVE,
        nullable=False,
    )


    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


    seller = relationship(
        "User",
        lazy="selectin",
    )


    files = relationship(
        "ProductFile",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


    @property
    def in_stock(self) -> bool:
        return self.available_quantity > 0



    def __repr__(self):

        return (
            f"<Product id={self.id} "
            f"title={self.title}>"
        )      
