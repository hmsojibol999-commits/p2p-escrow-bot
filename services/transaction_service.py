from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.transaction import Transaction, TransactionType, TransactionStatus


class TransactionService:
    """
    Financial Transaction & Ledger Service.
    Provides read-only queries, ledger log generation, financial summaries,
    and audit tracking for marketplace activities.
    """

    @staticmethod
    async def create_ledger_entry(
        session: AsyncSession,
        transaction_id: str,
        user_id: int,
        wallet_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
        fee: Decimal = Decimal("0.00"),
        status: TransactionStatus = TransactionStatus.SUCCESS,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Transaction:
        """
        Creates and stores an immutable transaction record in the ledger.
        """
        net_amount = amount - fee if transaction_type in [
            TransactionType.WITHDRAWAL,
            TransactionType.PURCHASE,
            TransactionType.COMMISSION
        ] else amount

        tx = Transaction(
            transaction_id=transaction_id,
            user_id=user_id,
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            status=status,
            reference_id=reference_id,
            description=description,
        )
        session.add(tx)
        await session.flush()
        return tx

    @staticmethod
    async def get_user_transactions(
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        tx_type: Optional[TransactionType] = None,
    ) -> Tuple[List[Transaction], int]:
        """
        Fetches paginated transactions for a specific user with optional type filtering.
        Returns a tuple of (transactions list, total_count).
        """
        # Base query
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        count_stmt = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)

        if tx_type:
            stmt = stmt.where(Transaction.transaction_type == tx_type)
            count_stmt = count_stmt.where(Transaction.transaction_type == tx_type)

        # Total count execution
        total_count = (await session.execute(count_stmt)).scalar() or 0

        # Paginated fetch ordered by creation date
        stmt = stmt.order_by(desc(Transaction.created_at)).offset(offset).limit(limit)
        results = await session.execute(stmt)
        transactions = list(results.scalars().all())

        return transactions, total_count

    @staticmethod
    async def get_user_financial_summary(
        session: AsyncSession, user_id: int
    ) -> Dict[str, Decimal]:
        """
        Calculates lifetime financial metrics for a user from the immutable ledger.
        """
        # Total Deposited
        dep_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.DEPOSIT,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        total_deposited = (await session.execute(dep_stmt)).scalar() or Decimal("0.00")

        # Total Withdrawn
        with_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        total_withdrawn = (await session.execute(with_stmt)).scalar() or Decimal("0.00")

        # Total Earned from Sales
        sale_stmt = select(func.coalesce(func.sum(Transaction.net_amount), Decimal("0.00"))).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.SALE,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        total_sales_income = (await session.execute(sale_stmt)).scalar() or Decimal("0.00")

        # Total Spent on Purchases
        purch_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.PURCHASE,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        total_spent = (await session.execute(purch_stmt)).scalar() or Decimal("0.00")

        return {
            "total_deposited": total_deposited,
            "total_withdrawn": total_withdrawn,
            "total_sales_income": total_sales_income,
            "total_spent": total_spent,
      }
      
