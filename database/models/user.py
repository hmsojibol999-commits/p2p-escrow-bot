from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    select,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.base import (
    Base,
    IDMixin,
    TimestampMixin,
)



class User(
    Base,
    IDMixin,
    TimestampMixin
):
    """
    Telegram User Database Model.
    Stores user identity, role, status and account information.
    """


    __tablename__ = "users"


    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )


    username: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )


    first_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )


    last_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )


    role: Mapped[str] = mapped_column(
        String(30),
        default="USER",
        nullable=False,
    )


    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


    # -------------------------
    # Helper Methods
    # -------------------------

    @classmethod
    async def get_by_telegram_id(
        cls,
        session: AsyncSession,
        telegram_id: int
    ) -> Optional["User"]:

        stmt = select(cls).where(
            cls.telegram_id == telegram_id
        )

        result = await session.execute(stmt)

        return result.scalar_one_or_none()


    @property
    def full_name(self) -> str:

        parts = [
            self.first_name,
            self.last_name
        ]

        return " ".join(
            p for p in parts if p
        ) or "User"


    def __repr__(self):

        return (
            f"<User id={self.id} "
            f"telegram_id={self.telegram_id}>"
        )
