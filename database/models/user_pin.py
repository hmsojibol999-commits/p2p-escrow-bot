from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.user import User


class UserPin(BaseModel):
    """
    User Security PIN Management Database Model.
    Stores securely hashed user security PINs for transaction authentication (e.g. Withdrawals),
    tracks brute-force attempt limits, account lockout windows, and PIN reset workflows.
    """

    __tablename__ = "user_pins"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
        description="Foreign key referencing users table primary key",
    )

    # ------------------------------------------------------------------
    # 2. PIN SECURE STORAGE (Hashed Only - Never Plaintext)
    # ------------------------------------------------------------------
    pin_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Bcrypt/Argon2 salted hash of the 4-6 digit Security PIN",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        description="Active status flag for the PIN security requirement",
    )

    # ------------------------------------------------------------------
    # 3. BRUTE FORCE & SECURITY TRACKING
    # ------------------------------------------------------------------
    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        description="Count of consecutive failed PIN verification attempts",
    )
    last_failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp of the last failed PIN verification attempt",
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp until which PIN verification is locked due to excess failures",
    )

    # ------------------------------------------------------------------
    # 4. RESET VERIFICATION WORKFLOW
    # ------------------------------------------------------------------
    reset_requested: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag denoting if user initiated a forgotten PIN reset request",
    )
    reset_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        description="Flag denoting if multi-factor or admin verification was completed for reset",
    )

    # ------------------------------------------------------------------
    # 5. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", backref="pin_security", uselist=False)

    # ------------------------------------------------------------------
    # HELPER PROPERTIES FOR SECURITY LOGIC
    # ------------------------------------------------------------------
    @property
    def is_locked(self) -> bool:
        """Returns True if PIN verification is currently locked due to bad attempts."""
        if self.locked_until and datetime.now(self.locked_until.tzinfo) < self.locked_until:
            return True
        return False

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED QUERYING
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_user_pin_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserPin(id={self.id}, user_id={self.user_id}, "
            f"is_active={self.is_active}, failed_attempts={self.failed_attempts})>"
        )
      
