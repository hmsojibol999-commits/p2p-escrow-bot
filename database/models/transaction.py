from decimal import Decimal
from typing import Optional

from sqlalchemy import (
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



class TransactionType(str, enum.Enum):

    DEPOSIT = "DEPOSIT"

    WITHDRAW = "WITHDRAW"

    TRANSFER_IN = "TRANSFER_IN"

    TRANSFER_OUT = "TRANSFER_OUT"

    ESCROW_HOLD = "ESCROW_HOLD"

    ESCROW_RELEASE = "ESCROW_RELEASE"

    REFUND = "REFUND"

    SALE = "SALE"



class TransactionStatus(str, enum.Enum):

    PENDING = "PENDING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"

    CANCELLED = "CANCELLED"



class Transaction(
    Base,
    IDMixin,
    TimestampMixin
):

    """
    Financial Ledger Model.
    Stores every wallet-related transaction permanently.
    """


    __tablename__ = "transactions"



    transaction_id: Mapped[str] = mapped_column(
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


    wallet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "wallets.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )


    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType),
        nullable=False,
    )


    amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    fee: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        default=Decimal("0.00"),
        nullable=False,
    )


    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
    )


    reference_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )


    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


    user = relationship(
        "User",
        lazy="selectin",
    )


    wallet = relationship(
        "Wallet",
        lazy="selectin",
    )



    def __repr__(self):

        return (
            f"<Transaction id={self.id} "
            f"type={self.transaction_type} "
            f"status={self.status}>"
        )
