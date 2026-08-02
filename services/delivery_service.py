from typing import Tuple, Optional, List
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.product import Product, ProductStatus, DeliveryMode
from database.models.product_file import ProductFile
from database.models.delivery import Delivery
from database.models.order import Order, OrderStatus


class DeliveryService:
    """
    Automated Payload Assignment & Digital Delivery Engine.
    Handles assigning digital keys, credentials, or uploaded stock files to buyers
    upon successful checkout and manages delivery verification logs.
    """

    @staticmethod
    async def assign_instant_payload(
        session: AsyncSession,
        order_id: int,
        buyer_id: int,
        product_id: int,
        quantity: int = 1,
    ) -> Tuple[bool, str, List[str]]:
        """
        Atomically assigns available stock files/payloads to an order and marks them as sold.
        Returns a tuple of (success_flag, status_message, list_of_payload_contents).
        """
        # Fetch Product
        prod_stmt = select(Product).where(Product.id == product_id).with_for_update()
        prod_res = await session.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()

        if not product or product.status != ProductStatus.ACTIVE:
            return False, "Product is no longer active or available for sale.", []

        if product.available_quantity < quantity:
            return False, f"Insufficient stock available. Requested: {quantity}, Available: {product.available_quantity}", []

        # Query unassigned stock items for this product
        file_stmt = (
            select(ProductFile)
            .where(
                ProductFile.product_id == product.id,
                ProductFile.is_sold == False,
            )
            .limit(quantity)
            .with_for_update()
        )
        files_res = await session.execute(file_stmt)
        available_files = list(files_res.scalars().all())

        if len(available_files) < quantity:
            return False, "Stock mismatch: Sufficient file payload entries were not found.", []

        delivered_contents: List[str] = []

        for p_file in available_files:
            # Mark file payload as sold
            p_file.is_sold = True
            p_file.sold_to_user_id = buyer_id
            p_file.order_id = order_id
            
            # Extract text content / Telegram File ID
            payload_data = p_file.file_content or p_file.file_id or p_file.secret_data or "N/A"
            delivered_contents.append(payload_data)

            # Record Delivery Log Entry
            delivery_log = Delivery(
                delivery_id=f"DLV-ORD-{order_id}-{p_file.id}",
                order_id=order_id,
                product_id=product.id,
                buyer_id=buyer_id,
                seller_id=product.seller_id,
                payload_data=payload_data,
                delivered_at=datetime.now(timezone.utc),
            )
            session.add(delivery_log)

        # Update Product Stock Counters
        product.sold_quantity += quantity
        if product.available_quantity == 0:
            product.status = ProductStatus.SOLD_OUT

        await session.commit()
        return True, f"Successfully assigned {quantity} item(s).", delivered_contents

    @staticmethod
    async def get_order_deliveries(
        session: AsyncSession, order_id: int
    ) -> List[Delivery]:
        """
        Retrieves all delivery logs associated with a specific order ID.
        """
        stmt = select(Delivery).where(Delivery.order_id == order_id)
        res = await session.execute(stmt)
        return list(res.scalars().all())
      
