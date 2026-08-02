from decimal import Decimal
from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.wallet import Wallet, WalletStatus
from database.models.transaction import Transaction, TransactionType, TransactionStatus
from database.models.deposit import Deposit, DepositStatus
from database.models.withdraw import Withdraw, WithdrawStatus
from database.models.transfer import Transfer, TransferStatus


class WalletService:
    """
    Core Financial Service Engine.
    Handles wallet querying, atomic balance modifications, deposits, payouts,
    and peer-to-peer transfers using database row locks to eliminate race conditions.
    """

    @staticmethod
    async def get_or_create_wallet(session: AsyncSession, user_id: int) -> Wallet:
        """
        Retrieves user's wallet or safely creates one if missing.
        """
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = Wallet(user_id=user_id)
            session.add(wallet)
            await session.flush()

        return wallet

    @staticmethod
    async def process_deposit_approval(
        session: AsyncSession, deposit_id: str, admin_id: int
    ) -> Tuple[bool, str]:
        """
        Approves a deposit request, credits the user's wallet balance atomically,
        and records a ledger entry.
        """
        # Fetch deposit record with lock
        stmt = select(Deposit).where(Deposit.deposit_id == deposit_id).with_for_update()
        result = await session.execute(stmt)
        deposit = result.scalar_one_or_none()

        if not deposit:
            return False, "Deposit record not found."
        if deposit.status != DepositStatus.PENDING:
            return False, f"Deposit is already processed with status: {deposit.status.value}."

        # Fetch and lock user wallet
        wallet_stmt = select(Wallet).where(Wallet.user_id == deposit.user_id).with_for_update()
        wallet_res = await session.execute(wallet_stmt)
        wallet = wallet_res.scalar_one_or_none()

        if not wallet:
            return False, "User wallet not found."
        if wallet.status != WalletStatus.ACTIVE:
            return False, "User wallet is currently restricted or frozen."

        # Update Wallet Balance
        deposit_amount = Decimal(str(deposit.amount))
        wallet.balance += deposit_amount
        wallet.total_deposited += deposit_amount

        # Update Deposit Record
        deposit.status = DepositStatus.APPROVED
        deposit.approved_by = admin_id
        deposit.processed_at = datetime.now(timezone.utc)

        # Create Financial Ledger Entry
        tx = Transaction(
            transaction_id=f"TX-DEP-{deposit.deposit_id}",
            user_id=deposit.user_id,
            wallet_id=wallet.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=deposit_amount,
            fee=Decimal("0.00"),
            net_amount=deposit_amount,
            status=TransactionStatus.SUCCESS,
            reference_id=deposit.deposit_id,
            description=f"Deposit via {deposit.payment_method.value} approved by admin ID {admin_id}",
        )
        session.add(tx)

        await session.commit()
        return True, "Deposit approved and wallet credited successfully."

    @staticmethod
    async def process_transfer(
        session: AsyncSession,
        sender_user_id: int,
        receiver_user_id: int,
        amount: Decimal,
        transfer_id: str,
        note: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Executes a secure atomic P2P fund transfer between two users.
        """
        if sender_user_id == receiver_user_id:
            return False, "Cannot transfer balance to your own account."

        if amount <= Decimal("0.00"):
            return False, "Transfer amount must be strictly greater than zero."

        # Acquire locks in deterministic order based on ID to prevent deadlocks
        first_id, second_id = sorted([sender_user_id, receiver_user_id])

        first_stmt = select(Wallet).where(Wallet.user_id == first_id).with_for_update()
        second_stmt = select(Wallet).where(Wallet.user_id == second_id).with_for_update()

        first_wallet = (await session.execute(first_stmt)).scalar_one_or_none()
        second_wallet = (await session.execute(second_stmt)).scalar_one_or_none()

        sender_wallet = first_wallet if first_id == sender_user_id else second_wallet
        receiver_wallet = first_wallet if first_id == receiver_user_id else second_wallet

        if not sender_wallet or not receiver_wallet:
            return False, "One or both user wallets could not be located."

        if sender_wallet.status != WalletStatus.ACTIVE or receiver_wallet.status != WalletStatus.ACTIVE:
            return False, "Transfer failed. One or both wallets are inactive or suspended."

        if sender_wallet.balance < amount:
            return False, "Insufficient balance for this transfer."

        # Perform atomic deduction and addition
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount

        # Record Transfer Object
        transfer_record = Transfer(
            transfer_id=transfer_id,
            sender_user_id=sender_user_id,
            receiver_user_id=receiver_user_id,
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=amount,
            status=TransferStatus.COMPLETED,
            transfer_note=note,
            completed_at=datetime.now(timezone.utc),
        )
        session.add(transfer_record)

        # Record Ledger entries for both users
        sender_tx = Transaction(
            transaction_id=f"TX-OUT-{transfer_id}",
            user_id=sender_user_id,
            wallet_id=sender_wallet.id,
            transaction_type=TransactionType.TRANSFER_OUT,
            amount=amount,
            fee=Decimal("0.00"),
            net_amount=amount,
            status=TransactionStatus.SUCCESS,
            reference_id=transfer_id,
            description=f"P2P Transfer sent to User ID {receiver_user_id}",
        )
        receiver_tx = Transaction(
            transaction_id=f"TX-IN-{transfer_id}",
            user_id=receiver_user_id,
            wallet_id=receiver_wallet.id,
            transaction_type=TransactionType.TRANSFER_IN,
            amount=amount,
            fee=Decimal("0.00"),
            net_amount=amount,
            status=TransactionStatus.SUCCESS,
            reference_id=transfer_id,
            description=f"P2P Transfer received from User ID {sender_user_id}",
        )

        session.add_all([sender_tx, receiver_tx])
        await session.commit()

        return True, "Balance transferred successfully."
      
