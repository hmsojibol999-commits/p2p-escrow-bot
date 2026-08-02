from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Numeric,
    String,
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



class WalletStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    DISABLED = "DISABLED"



class Wallet(
    Base,
    IDMixin,
    TimestampMixin
):
    """
    User Financial Wallet Model.
    Handles balance, escrow holding and earning records.
    """


    __tablename__ = "wallets"


    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False,
        index=True,
    )


    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )


    escrow_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )


    total_deposited: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )


    total_earned: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )


    status: Mapped[WalletStatus] = mapped_column(
        Enum(WalletStatus),
        default=WalletStatus.ACTIVE,
        nullable=False,
    )


    # Relationship
    user = relationship(
        "User",
        backref="wallet",
        lazy="selectin"
    )


    @property
    def available_balance(self) -> Decimal:
        """
        Returns spendable balance.
        """
        return self.balance



    def __repr__(self):

        return (
            f"<Wallet id={self.id} "
            f"user_id={self.user_id} "
            f"balance={self.balance}>"
        )
