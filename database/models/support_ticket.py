import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# File 004 (database/base.py) থেকে BaseModel ইমপোর্ট
from database.base import BaseModel

if TYPE_CHECKING:
    from database.models.user import User


# ------------------------------------------------------------------
# ENUMS FOR TICKET STATUS & PRIORITY
# ------------------------------------------------------------------
class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class SupportTicket(BaseModel):
    """
    Support Ticket Database Model.
    Allows users (buyers/sellers) to submit help requests, bug reports, or general inquiries
    to administrators and support staff.
    """

    __tablename__ = "support_tickets"

    # ------------------------------------------------------------------
    # 1. BASIC IDENTIFIERS & FOREIGN KEYS
    # ------------------------------------------------------------------
    ticket_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        description="Unique support ticket identifier (e.g., TCK-XXXXXXXX)",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        description="Foreign key referencing the user who created the support ticket",
    )
    assigned_admin_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        description="Telegram ID or User ID of the admin/support agent handling this ticket",
    )

    # ------------------------------------------------------------------
    # 2. TICKET CONTENT & CATEGORIZATION
    # ------------------------------------------------------------------
    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        description="Short summary or title of the issue",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default="GENERAL",
        nullable=False,
        description="Category of ticket (e.g. PAYMENT, ORDER, ACCOUNT, BUG_REPORT)",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        description="Detailed description of the problem or request",
    )
    attachment_file_id: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        description="Telegram File ID or image proof attached with ticket",
    )

    # ------------------------------------------------------------------
    # 3. STATUS & PRIORITY CONTROL
    # ------------------------------------------------------------------
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, name="ticket_status_enum"),
        default=TicketStatus.OPEN,
        index=True,
        nullable=False,
        description="Lifecycle state of ticket (OPEN, IN_PROGRESS, RESOLVED, CLOSED)",
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SQLEnum(TicketPriority, name="ticket_priority_enum"),
        default=TicketPriority.MEDIUM,
        nullable=False,
        description="Priority level set by user or admin (LOW, MEDIUM, HIGH, URGENT)",
    )

    # ------------------------------------------------------------------
    # 4. RESOLUTION DETAILS
    # ------------------------------------------------------------------
    admin_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        description="Official answer or note provided by admin/support team",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        description="Timestamp when the ticket was marked as resolved or closed",
    )

    # ------------------------------------------------------------------
    # 5. RELATIONSHIPS
    # ------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", backref="support_tickets")

    # ------------------------------------------------------------------
    # INDEXES FOR OPTIMIZED ADMIN SEARCH
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_ticket_user_status", "user_id", "status"),
        Index("idx_ticket_status_priority", "status", "priority"),
    )

    def __repr__(self) -> str:
        return (
            f"<SupportTicket(id={self.id}, ticket_id='{self.ticket_id}', "
            f"user_id={self.user_id}, status='{self.status.value}', priority='{self.priority.value}')>"
        )
      
