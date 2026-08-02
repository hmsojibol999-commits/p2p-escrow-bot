from typing import Tuple, Optional, List
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.dispute import Dispute, DisputeStatus
from database.models.order import Order, OrderStatus
from database.models.escrow import Escrow, EscrowStatus
from services.escrow_service import EscrowService


class DisputeService:
    """
    Dispute Management & Case Resolution Engine.
    Handles buyer/seller grievance registration, evidence storage,
    and admin verdict executions (refunding or releasing funds).
    """

    @staticmethod
    async def open_dispute(
        session: AsyncSession,
        dispute_id: str,
        order_id: int,
        opened_by_user_id: int,
        reason: str,
        evidence_file_id: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Dispute]]:
        """
        Opens a new dispute for an order and updates the order status to UNDER_DISPUTE.
        """
        # Verify order existence and eligibility
        stmt = select(Order).where(Order.id == order_id).with_for_update()
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return False, "Order record not found.", None

        if opened_by_user_id not in [order.buyer_id, order.seller_id]:
            return False, "You are not authorized to open a dispute for this order.", None

        if order.status in [OrderStatus.CANCELLED, OrderStatus.REFUNDED]:
            return False, "Cannot open dispute on a cancelled or refunded order.", None

        # Check if an active dispute already exists
        disp_stmt = select(Dispute).where(Dispute.order_id == order_id)
        existing_dispute = (await session.execute(disp_stmt)).scalar_one_or_none()

        if existing_dispute and existing_dispute.status == DisputeStatus.OPEN:
            return False, "An active dispute is already open for this order.", None

        # Create new Dispute record
        dispute = Dispute(
            dispute_id=dispute_id,
            order_id=order_id,
            opened_by_user_id=opened_by_user_id,
            reason=reason,
            evidence_file_id=evidence_file_id,
            status=DisputeStatus.OPEN,
        )
        session.add(dispute)

        # Mark order as under dispute
        order.status = OrderStatus.UNDER_DISPUTE

        await session.commit()
        return True, "Dispute opened successfully. Under investigation.", dispute

    @staticmethod
    async def resolve_dispute_by_admin(
        session: AsyncSession,
        dispute_id: str,
        admin_id: int,
        refund_to_buyer: bool,
        admin_notes: str,
    ) -> Tuple[bool, str]:
        """
        Executes admin verdict for a dispute.
        If refund_to_buyer is True, full escrow amount is returned to buyer.
        If False, funds are released to the seller.
        """
        stmt = select(Dispute).where(Dispute.dispute_id == dispute_id).with_for_update()
        result = await session.execute(stmt)
        dispute = result.scalar_one_or_none()

        if not dispute or dispute.status != DisputeStatus.OPEN:
            return False, "Active dispute record not found."

        # Fetch associated Order and Escrow
        order_stmt = select(Order).where(Order.id == dispute.order_id).with_for_update()
        order = (await session.execute(order_stmt)).scalar_one_or_none()

        if not order:
            return False, "Associated order record not found."

        escrow_stmt = select(Escrow).where(Escrow.order_id == order.id)
        escrow = (await session.execute(escrow_stmt)).scalar_one_or_none()

        if not escrow:
            return False, "Associated escrow record not found."

        # Execute decision
        if refund_to_buyer:
            success, msg = await EscrowService.refund_escrow_to_buyer(
                session=session,
                escrow_id=escrow.escrow_id,
                reason=f"Admin Verdict (Dispute ID: {dispute_id}): {admin_notes}",
            )
            if success:
                order.status = OrderStatus.REFUNDED
                dispute.status = DisputeStatus.RESOLVED_BUYER
        else:
            success, msg = await EscrowService.release_escrow_payout(
                session=session,
                escrow_id=escrow.escrow_id,
            )
            if success:
                order.status = OrderStatus.COMPLETED
                dispute.status = DisputeStatus.RESOLVED_SELLER

        if not success:
            return False, f"Failed to execute financial resolution: {msg}"

        # Record admin resolution metadata
        dispute.admin_notes = admin_notes
        dispute.resolved_by_admin_id = admin_id
        dispute.resolved_at = datetime.now(timezone.utc)

        await session.commit()
        return True, f"Dispute successfully resolved. Decision: {'Refunded Buyer' if refund_to_buyer else 'Released to Seller'}."
          
