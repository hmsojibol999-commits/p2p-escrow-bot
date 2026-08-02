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

from datetime import datetime



class TransferStatus(str, enum.Enum):

    PENDING = "PENDING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"

    CANCELLED = "CANCELLED"



class Transfer(
    Base,
    IDMixin,
    TimestampMixin
):

    """
    Internal Wallet Transfer Model.
    Stores user-to-user balance transfer history.
    """


    __tablename__ = "transfers"



    transfer_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )


    sender_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    receiver_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )


    sender_wallet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "wallets.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )


    receiver_wallet_id: Mapped[int] = mapped_column(
        ForeignKey(
            "wallets.id",
            ondelete="CASCADE"
        ),
        nullable=False,
    )


    amount: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        nullable=False,
    )


    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus),
        default=TransferStatus.PENDING,
        nullable=False,
    )


    transfer_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )


    sender = relationship(
        "User",
        foreign_keys=[sender_user_id],
        lazy="selectin",
    )


    receiver = relationship(
        "User",
        foreign_keys=[receiver_user_id],
        lazy="selectin",
    )


    def __repr__(self):

        return (
            f"<Transfer id={self.id} "
            f"status={self.status}>"
        )
