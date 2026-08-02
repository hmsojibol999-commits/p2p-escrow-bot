from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.x Declarative Base Class.
    All database models will inherit from this Base class.
    Compatible with Alembic migrations and async database sessions.
    """

    pass


class BaseModel(Base):
    """
    Abstract Base Model offering common column fields, timezone-aware timestamps,
    and string representation for debugging and logging.
    """

    __abstract__ = True

    # 1. Primary Key: Auto-incrementing Integer ID
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )

    # 2. Created Time: Auto-populated on creation
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        description="Timestamp when the record was created",
    )

    # 3. Updated Time: Auto-populated on creation and auto-updated on change
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        description="Timestamp when the record was last updated",
    )

    def __repr__(self) -> str:
        """
        Clean, informative dynamic string representation for debugging and logging.
        Automatically prints class name and primary ID.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict[str, Any]:
        """
        Helper method to convert model instance attributes into a python dictionary.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        
