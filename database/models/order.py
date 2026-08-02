from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    Numeric,
    Enum,
    ForeignKey,
    Text,
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



class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    UNDER_DISPUTE = "UNDER_DISPUTE"



class Order(
    Base,
    IDMixin,
    TimestampMixin
):
    """
    Marketplace Order Model.
    Controls buyer, seller, product, payment and delivery lifecycle.
    """


    __tablename__ = "orders"


    order_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )


    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )


    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )


    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
    )


    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


    # Relationships

    buyer = relationship(
        "User",
        foreign_keys=[buyer_id],
        lazy="selectin",
    )


    seller = relationship(
        "User",
        foreign_keys=[seller_id],
        lazy="selectin",
    )


    product = relationship(
        "Product",
        lazy="selectin",
    )



    @property
    def is_finished(self) -> bool:
        return self.status in [
            OrderStatus.COMPLETED,
            OrderStatus.REFUNDED,
            OrderStatus.CANCELLED,
        ]



    def __repr__(self):

        return (
            f"<Order id={self.id} "
            f"order_id={self.order_id} "
            f"status={self.status}>"
        )
