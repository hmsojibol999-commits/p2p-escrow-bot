from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String,
    Numeric,
    Enum,
    ForeignKey,
    BigInteger,
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



class PaymentMethod(str, enum.Enum):

    BKASH = "BKASH"

    NAGAD = "NAGAD"

    ROCKET = "ROCKET"

    BINANCE_PAY = "BINANCE_PAY"

    CRYPTO = "CRYPTO"



class DepositStatus(str, enum.Enum):

    PENDING = "PENDING"

    APPROVED = "APPROVED"

    REJECTED = "REJECTED"



class Deposit(
    Base,
    IDMixin,
    TimestampMixin
):

    """
    User Deposit Request Model.
    Handles manual and crypto deposit verification.
    """


    __tablename__ = "deposits"



    deposit_id: Mapped[str] = mapped_column(
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


    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod),
        nullable=False,
    )


    amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    currency: Mapped[str] = mapped_column(
        String(10),
        default="BDT",
        nullable=False,
    )


    transaction_id_claim: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )


    sender_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )


    status: Mapped[DepositStatus] = mapped_column(
        Enum(DepositStatus),
        default=DepositStatus.PENDING,
        nullable=False,
    )


    approved_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )


    processed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )


    user = relationship(
        "User",
        lazy="selectin",
    )



    def __repr__(self):

        return (
            f"<Deposit id={self.id} "
            f"status={self.status}>"
        )
