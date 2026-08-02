# ==========================================================
# P2P ESCROW MARKETPLACE BOT
#
# File    : services/wallet_service.py
# Module  : Wallet Financial Engine
# Version : V1.0.0
# ==========================================================

from decimal import Decimal
from typing import Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.wallet import Wallet, WalletStatus
from database.models.transaction import (
    Transaction,
    TransactionType,
    TransactionStatus
)

from database.models.deposit import (
    Deposit,
    DepositStatus
)

from database.models.transfer import (
    Transfer,
    TransferStatus
)



class WalletService:
    """
    Core wallet management service.
    Handles balance operations, deposits and transfers.
    """


    @staticmethod
    async def get_or_create_wallet(
        session: AsyncSession,
        user_id: int
    ) -> Wallet:

        stmt = select(Wallet).where(
            Wallet.user_id == user_id
        )

        result = await session.execute(stmt)

        wallet = result.scalar_one_or_none()


        if not wallet:

            wallet = Wallet(
                user_id=user_id,
                balance=Decimal("0.00"),
                escrow_balance=Decimal("0.00"),
                total_deposited=Decimal("0.00"),
                total_earned=Decimal("0.00")
            )

            session.add(wallet)

            await session.flush()


        return wallet



    @staticmethod
    async def process_deposit_approval(
        session: AsyncSession,
        deposit_id: str,
        admin_id: int
    ) -> Tuple[bool, str]:


        stmt = (
            select(Deposit)
            .where(
                Deposit.deposit_id == deposit_id
            )
            .with_for_update()
        )


        result = await session.execute(stmt)

        deposit = result.scalar_one_or_none()


        if not deposit:
            return False, "Deposit not found."


        if deposit.status != DepositStatus.PENDING:
            return False, "Deposit already processed."



        wallet_stmt = (
            select(Wallet)
            .where(
                Wallet.user_id == deposit.user_id
            )
            .with_for_update()
        )


        wallet = (
            await session.execute(wallet_stmt)
        ).scalar_one_or_none()



        if not wallet:
            return False, "Wallet not found."



        amount = Decimal(str(deposit.amount))


        wallet.balance += amount

        wallet.total_deposited += amount



        deposit.status = DepositStatus.APPROVED

        deposit.approved_by = admin_id

        deposit.processed_at = datetime.now(
            timezone.utc
        )



        transaction = Transaction(
            transaction_id=f"DEP-{deposit.deposit_id}",
            user_id=deposit.user_id,
            wallet_id=wallet.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            fee=Decimal("0.00"),
            net_amount=amount,
            status=TransactionStatus.SUCCESS,
            reference_id=deposit.deposit_id,
            description="Deposit approved"
        )


        session.add(transaction)


        await session.flush()


        return True, "Deposit approved successfully."




    @staticmethod
    async def process_transfer(
        session: AsyncSession,
        sender_user_id: int,
        receiver_user_id: int,
        amount: Decimal,
        transfer_id: str,
        note: Optional[str] = None
    ) -> Tuple[bool, str]:


        if sender_user_id == receiver_user_id:
            return False, "Cannot transfer to yourself."


        if amount <= Decimal("0"):
            return False, "Invalid amount."



        first, second = sorted(
            [
                sender_user_id,
                receiver_user_id
            ]
        )


        wallets = []


        for uid in [first, second]:

            stmt = (
                select(Wallet)
                .where(
                    Wallet.user_id == uid
                )
                .with_for_update()
            )

            wallet = (
                await session.execute(stmt)
            ).scalar_one_or_none()


            if not wallet:
                return False, "Wallet missing."


            wallets.append(wallet)



        sender_wallet = (
            wallets[0]
            if first == sender_user_id
            else wallets[1]
        )


        receiver_wallet = (
            wallets[0]
            if first == receiver_user_id
            else wallets[1]
        )



        if sender_wallet.balance < amount:
            return False, "Insufficient balance."



        sender_wallet.balance -= amount

        receiver_wallet.balance += amount



        transfer = Transfer(
            transfer_id=transfer_id,
            sender_user_id=sender_user_id,
            receiver_user_id=receiver_user_id,
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=amount,
            status=TransferStatus.COMPLETED,
            transfer_note=note,
            completed_at=datetime.now(timezone.utc)
        )


        session.add(transfer)



        session.add_all([

            Transaction(
                transaction_id=f"OUT-{transfer_id}",
                user_id=sender_user_id,
                wallet_id=sender_wallet.id,
                transaction_type=TransactionType.TRANSFER_OUT,
                amount=amount,
                fee=Decimal("0.00"),
                net_amount=amount,
                status=TransactionStatus.SUCCESS,
                reference_id=transfer_id
            ),


            Transaction(
                transaction_id=f"IN-{transfer_id}",
                user_id=receiver_user_id,
                wallet_id=receiver_wallet.id,
                transaction_type=TransactionType.TRANSFER_IN,
                amount=amount,
                fee=Decimal("0.00"),
                net_amount=amount,
                status=TransactionStatus.SUCCESS,
                reference_id=transfer_id
            )

        ])



        await session.flush()


        return True, "Transfer completed."



    @staticmethod
    async def transfer_funds(
        session: AsyncSession,
        sender_user_id: int,
        receiver_user_id: int,
        amount: Decimal
    ) -> Tuple[bool, str]:

        return await WalletService.process_transfer(
            session,
            sender_user_id,
            receiver_user_id,
            amount,
            transfer_id=f"TRX-{datetime.now().timestamp()}"
            )
