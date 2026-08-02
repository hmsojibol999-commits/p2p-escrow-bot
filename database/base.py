from datetime import datetime, timezone

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from sqlalchemy import (
    DateTime,
    Integer,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy Base Class.
    All database models inherit from this class.
    """
    pass



class TimestampMixin:
    """
    Automatic created_at and updated_at fields
    for all database tables.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )



class IDMixin:
    """
    Universal integer primary key.
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
