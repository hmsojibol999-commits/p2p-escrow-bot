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



class WithdrawStatus(str, enum.Enum):

    PENDING = "PENDING"

    APPROVED = "APPROVED"

    REJECTED = "REJECTED"

    CANCELLED = "CANCELLED"



class Withdraw(
    Base,
    IDMixin,
    TimestampMixin
):

    """
    User Withdrawal Request Model.
    Handles payout requests and admin processing.
    """


    __tablename__ = "withdraws"



    withdraw_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    account_details: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    status: Mapped[WithdrawStatus] = mapped_column(
        Enum(WithdrawStatus),
        default=WithdrawStatus.PENDING,
        nullable=False,
    )


    approved_by: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )


    processed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )


    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )


    user = relationship(
        "User",
        lazy="selectin",
    )



    def __repr__(self):

        return (
            f"<Withdraw id={self.id} "
            f"status={self.status}>"
        )
