from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String,
    Numeric,
    Enum,
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

from datetime import datetime



class EscrowStatus(str, enum.Enum):
    HELD = "HELD"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"



class Escrow(
    Base,
    IDMixin,
    TimestampMixin
):
    """
    Escrow Transaction Model.
    Holds buyer payment until order completion or dispute resolution.
    """


    __tablename__ = "escrows"



    escrow_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )


    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )


    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )


    amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    status: Mapped[EscrowStatus] = mapped_column(
        Enum(EscrowStatus),
        default=EscrowStatus.HELD,
        nullable=False,
    )


    released_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )


    order = relationship(
        "Order",
        lazy="selectin",
    )


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


    def is_active(self) -> bool:
        return self.status == EscrowStatus.HELD



    def __repr__(self):

        return (
            f"<Escrow id={self.id} "
            f"status={self.status}>"
        )
