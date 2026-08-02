from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.product import Product
from database.models.transaction import Transaction, TransactionType, TransactionStatus


class CommissionService:
    """
    Platform Revenue & Sales Commission Engine.
    Calculates dynamic fees for orders, processes overrides, and generates admin income reports.
    """

    # System default platform commission percentage (e.g. 5.00%)
    DEFAULT_COMMISSION_RATE = Decimal("5.00")

    @classmethod
    def calculate_commission(
        cls, amount: Decimal, custom_rate: Optional[Decimal] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculates commission fee and net seller payout for a given amount.
        Returns a tuple: (commission_amount, net_payout_amount)
        """
        rate = custom_rate if custom_rate is not None and custom_rate >= Decimal("0.00") else cls.DEFAULT_COMMISSION_RATE
        
        # Calculate fee with standard financial rounding
        commission_amount = (amount * rate / Decimal("100.00")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        net_payout = amount - commission_amount

        return commission_amount, net_payout

    @staticmethod
    async def get_product_effective_rate(
        session: AsyncSession, product_id: int
    ) -> Decimal:
        """
        Retrieves the effective commission rate for a product (product override or global default).
        """
        stmt = select(Product.commission_rate).where(Product.id == product_id)
        result = await session.execute(stmt)
        rate = result.scalar_one_or_none()

        if rate is not None and rate > Decimal("0.00"):
            return Decimal(str(rate))
        
        return CommissionService.DEFAULT_COMMISSION_RATE

    @staticmethod
    async def get_total_platform_revenue(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Calculates total historical platform commission revenue from successful sales transactions.
        """
        stmt = select(
            func.coalesce(func.sum(Transaction.fee), Decimal("0.00")),
            func.count(Transaction.id)
        ).where(
            Transaction.transaction_type == TransactionType.SALE,
            Transaction.status == TransactionStatus.SUCCESS
        )
        
        result = await session.execute(stmt)
        total_revenue, total_sales_count = result.one()

        return {
            "total_commission_earned": Decimal(str(total_revenue)),
            "total_successful_sales": total_sales_count,
            "default_rate_percent": CommissionService.DEFAULT_COMMISSION_RATE
        }

