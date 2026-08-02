from decimal import Decimal
from typing import Tuple, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deposit import Deposit, DepositStatus, PaymentMethod


class ManualPaymentGateway:
    """
    Manual Local Gateway Service Processor (Bkash, Nagad, Rocket).
    Validates transaction claims (TrxID) and manages pending deposits for admin approval.
    """

    SUPPORTED_METHODS = [
        PaymentMethod.BKASH,
        PaymentMethod.NAGAD,
        PaymentMethod.ROCKET,
    ]

    @staticmethod
    async def submit_deposit_request(
        session: AsyncSession,
        deposit_id: str,
        user_id: int,
        payment_method: PaymentMethod,
        amount: Decimal,
        transaction_id_claim: str,
        sender_account_number: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Deposit]]:
        """
        Submits a manual deposit claim for Bkash/Nagad/Rocket with unique TrxID verification.
        """
        if payment_method not in ManualPaymentGateway.SUPPORTED_METHODS:
            return False, f"Unsupported payment method: {payment_method.value}", None

        if amount <= Decimal("0.00"):
            return False, "Deposit amount must be strictly greater than zero.", None

        clean_trx_id = transaction_id_claim.strip().upper()
        if not clean_trx_id:
            return False, "Transaction ID (TrxID) cannot be empty.", None

        # Check for duplicate TrxID submissions across all deposits
        stmt = select(Deposit).where(Deposit.transaction_id_claim == clean_trx_id)
        existing_trx = (await session.execute(stmt)).scalar_one_or_none()

        if existing_trx:
            return False, "This Transaction ID (TrxID) has already been submitted or processed.", None

        # Create new Deposit Entry in PENDING status
        deposit = Deposit(
            deposit_id=deposit_id,
            user_id=user_id,
            payment_method=payment_method,
            amount=amount,
            currency="BDT",
            transaction_id_claim=clean_trx_id,
            sender_account_number=sender_account_number,
            status=DepositStatus.PENDING,
        )
        session.add(deposit)
        await session.commit()

        return True, "Manual deposit request submitted successfully. Awaiting admin approval.", deposit

    @staticmethod
    async def get_pending_manual_deposits(
        session: AsyncSession, limit: int = 20, offset: int = 0
    ) -> List[Deposit]:
        """
        Fetches pending manual deposit submissions for admin review.
        """
        stmt = (
            select(Deposit)
            .where(
                Deposit.status == DepositStatus.PENDING,
                Deposit.payment_method.in_(ManualPaymentGateway.SUPPORTED_METHODS),
            )
            .order_by(Deposit.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await session.execute(stmt)
        return list(results.scalars().all())

