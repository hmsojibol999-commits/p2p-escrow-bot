from decimal import Decimal
from typing import Tuple, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deposit import Deposit, DepositStatus, PaymentMethod


class CryptoPaymentGateway:
    """
    Binance & Crypto Gateway Service Processor.
    Manages Binance Pay ID / TxID deposit claims and verifies unique hash submissions.
    """

    SUPPORTED_METHODS = [
        PaymentMethod.BINANCE_PAY,
        PaymentMethod.CRYPTO,
    ]

    @staticmethod
    async def submit_crypto_deposit(
        session: AsyncSession,
        deposit_id: str,
        user_id: int,
        payment_method: PaymentMethod,
        amount: Decimal,
        transaction_hash_claim: str,
        sender_binance_id: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Deposit]]:
        """
        Submits a Binance Pay or Crypto deposit claim with unique TxID/Hash validation.
        """
        if payment_method not in CryptoPaymentGateway.SUPPORTED_METHODS:
            return False, f"Unsupported crypto payment method: {payment_method.value}", None

        if amount <= Decimal("0.00"):
            return False, "Deposit amount must be strictly greater than zero.", None

        clean_hash = transaction_hash_claim.strip()
        if not clean_hash:
            return False, "Binance Order ID / Transaction Hash cannot be empty.", None

        # Check for duplicate hash submissions
        stmt = select(Deposit).where(Deposit.transaction_id_claim == clean_hash)
        existing_tx = (await session.execute(stmt)).scalar_one_or_none()

        if existing_trx := existing_tx:
            return False, "This Binance/Crypto Transaction ID has already been submitted.", None

        # Create new Deposit Entry
        deposit = Deposit(
            deposit_id=deposit_id,
            user_id=user_id,
            payment_method=payment_method,
            amount=amount,
            currency="USDT",
            transaction_id_claim=clean_hash,
            sender_account_number=sender_binance_id,
            status=DepositStatus.PENDING,
        )
        session.add(deposit)
        await session.commit()

        return True, "Binance/Crypto deposit request submitted successfully. Awaiting verification.", deposit

    @staticmethod
    async def get_pending_crypto_deposits(
        session: AsyncSession, limit: int = 20, offset: int = 0
    ) -> List[Deposit]:
        """
        Fetches pending crypto deposit submissions for admin approval.
        """
        stmt = (
            select(Deposit)
            .where(
                Deposit.status == DepositStatus.PENDING,
                Deposit.payment_method.in_(CryptoPaymentGateway.SUPPORTED_METHODS),
            )
            .order_by(Deposit.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await session.execute(stmt)
        return list(results.scalars().all())

