from decimal import Decimal
from typing import Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.wallet import Wallet, WalletStatus
from database.models.escrow import Escrow, EscrowStatus
from database.models.order import Order, OrderStatus
from database.models.transaction import Transaction, TransactionType, TransactionStatus


class EscrowService:
    """
    Escrow Hold & Dispute Resolution Service Engine.
    Safely locks buyer funds upon order placement, releases payouts to sellers upon delivery confirmation,
    or refunds buyers in case of order cancellation/dispute resolution.
    """

    @staticmethod
    async def create_escrow_hold(
        session: AsyncSession,
        escrow_id: str,
        order_id: int,
        buyer_id: int,
        seller_id: int,
        amount: Decimal,
        hold_hours: int = 24,
    ) -> Tuple[bool, str]:
        """
        Deducts buyer liquid balance and transfers it to Escrow Hold Balance.
        """
        if amount <= Decimal("0.00"):
            return False, "Escrow hold amount must be greater than zero."

        # Lock buyer wallet row
        stmt = select(Wallet).where(Wallet.user_id == buyer_id).with_for_update()
        res = await session.execute(stmt)
        buyer_wallet = res.scalar_one_or_none()

        if not buyer_wallet or buyer_wallet.status != WalletStatus.ACTIVE:
            return False, "Buyer wallet is inactive or unavailable."

        if buyer_wallet.balance < amount:
            return False, "Insufficient liquid balance to initiate escrow hold."

        # Lock seller wallet row to ensure account readiness
        seller_stmt = select(Wallet).where(Wallet.user_id == seller_id).with_for_update()
        seller_res = await session.execute(seller_stmt)
        seller_wallet = seller_res.scalar_one_or_none()

        if not seller_wallet or seller_wallet.status != WalletStatus.ACTIVE:
            return False, "Seller wallet is restricted or unavailable."

        # Move balance to escrow hold
        buyer_wallet.balance -= amount
        buyer_wallet.escrow_balance += amount

        # Create Escrow record
        escrow = Escrow(
            escrow_id=escrow_id,
            order_id=order_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            amount=amount,
            status=EscrowStatus.HELD,
        )
        session.add(escrow)

        # Record Ledger Entry
        tx = Transaction(
            transaction_id=f"TX-ESC-HOLD-{escrow_id}",
            user_id=buyer_id,
            wallet_id=buyer_wallet.id,
            transaction_type=TransactionType.ESCROW_HOLD,
            amount=amount,
            fee=Decimal("0.00"),
            net_amount=amount,
            status=TransactionStatus.SUCCESS,
            reference_id=escrow_id,
            description=f"Escrow balance hold for Order ID #{order_id}",
        )
        session.add(tx)

        await session.commit()
        return True, "Funds successfully held in escrow."

    @staticmethod
    async def release_escrow_payout(
        session: AsyncSession,
        escrow_id: str,
        commission_rate: Decimal = Decimal("5.00"),
    ) -> Tuple[bool, str]:
        """
        Releases escrow hold balance, deducts platform sales commission,
        and transfers net earnings to the seller.
        """
        # Fetch Escrow record with lock
        stmt = select(Escrow).where(Escrow.escrow_id == escrow_id).with_for_update()
        res = await session.execute(stmt)
        escrow = res.scalar_one_or_none()

        if not escrow:
            return False, "Escrow record not found."
        if escrow.status != EscrowStatus.HELD:
            return False, f"Escrow cannot be released. Current status: {escrow.status.value}."

        # Acquire deterministic locks for buyer and seller wallets
        buyer_id, seller_id = escrow.buyer_id, escrow.seller_id
        first_id, second_id = sorted([buyer_id, seller_id])

        w1_stmt = select(Wallet).where(Wallet.user_id == first_id).with_for_update()
        w2_stmt = select(Wallet).where(Wallet.user_id == second_id).with_for_update()

        w1 = (await session.execute(w1_stmt)).scalar_one_or_none()
        w2 = (await session.execute(w2_stmt)).scalar_one_or_none()

        buyer_wallet = w1 if first_id == buyer_id else w2
        seller_wallet = w1 if first_id == seller_id else w2

        if not buyer_wallet or not seller_wallet:
            return False, "Unable to lock buyer or seller wallet."

        escrow_amount = escrow.amount

        if buyer_wallet.escrow_balance < escrow_amount:
            return False, "Inconsistent escrow hold balance."

        # Calculate Commission
        commission_amount = (escrow_amount * commission_rate) / Decimal("100.00")
        seller_net_payout = escrow_amount - commission_amount

        # Update Wallets
        buyer_wallet.escrow_balance -= escrow_amount
        seller_wallet.balance += seller_net_payout
        seller_wallet.total_earned += seller_net_payout

        # Update Escrow Status
        escrow.status = EscrowStatus.RELEASED
        escrow.released_at = datetime.now(timezone.utc)

        # Ledger Entries
        seller_tx = Transaction(
            transaction_id=f"TX-ESC-REL-{escrow_id}",
            user_id=seller_id,
            wallet_id=seller_wallet.id,
            transaction_type=TransactionType.SALE,
            amount=escrow_amount,
            fee=commission_amount,
            net_amount=seller_net_payout,
            status=TransactionStatus.SUCCESS,
            reference_id=escrow_id,
            description=f"Escrow payout released for Order #{escrow.order_id} (Commission: {commission_rate}%)",
        )
        session.add(seller_tx)

        await session.commit()
        return True, "Escrow funds successfully released to seller."

    @staticmethod
    async def refund_escrow_to_buyer(
        session: AsyncSession, escrow_id: str, reason: str = "Order Cancelled / Refunded"
    ) -> Tuple[bool, str]:
        """
        Cancels escrow hold and refunds full amount back to buyer's main balance.
        """
        stmt = select(Escrow).where(Escrow.escrow_id == escrow_id).with_for_update()
        res = await session.execute(stmt)
        escrow = res.scalar_one_or_none()

        if not escrow or escrow.status != EscrowStatus.HELD:
            return False, "Valid held escrow record not found."

        buyer_stmt = select(Wallet).where(Wallet.user_id == escrow.buyer_id).with_for_update()
        buyer_res = await session.execute(buyer_stmt)
        buyer_wallet = buyer_res.scalar_one_or_none()

        if not buyer_wallet:
            return False, "Buyer wallet not found."

        escrow_amount = escrow.amount

        # Move balance back
        buyer_wallet.escrow_balance -= escrow_amount
        buyer_wallet.balance += escrow_amount

        # Update Status
        escrow.status = EscrowStatus.REFUNDED
        escrow.released_at = datetime.now(timezone.utc)

        # Ledger Entry
        tx = Transaction(
            transaction_id=f"TX-ESC-REF-{escrow_id}",
            user_id=escrow.buyer_id,
            wallet_id=buyer_wallet.id,
            transaction_type=TransactionType.REFUND,
            amount=escrow_amount,
            fee=Decimal("0.00"),
            net_amount=escrow_amount,
            status=TransactionStatus.SUCCESS,
            reference_id=escrow_id,
            description=f"Full Escrow Refund for Order #{escrow.order_id}. Reason: {reason}",
        )
        session.add(tx)

        await session.commit()
        return True, "Escrow funds refunded to buyer successfully."
  
