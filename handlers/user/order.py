from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from database.models.user import User
from database.models.product import Product
from database.models.order import Order, OrderStatus
from database.models.escrow import Escrow, EscrowStatus
from services.escrow_service import EscrowService
from services.delivery_service import DeliveryService
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data.startswith("order_buy_"))
async def cb_create_order(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Initiates a secure escrow purchase for the selected product.
    """
    try:
        product_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Invalid product selection.", show_alert=True)
        return

    stmt = select(Product).where(Product.id == product_id)
    product = (await db_session.execute(stmt)).scalar_one_or_none()

    if not product:
        await callback.answer("Product not found.", show_alert=True)
        return

    if product.seller_id == db_user.id:
        await callback.answer("❌ You cannot purchase your own listed product.", show_alert=True)
        return

    order_id_str = f"ORD-{secrets.token_hex(4).upper()}"
    escrow_id_str = f"ESC-{secrets.token_hex(4).upper()}"

    # Create order via EscrowService
    success, msg, order, escrow = await EscrowService.create_escrow_order(
        session=db_session,
        order_id=order_id_str,
        escrow_id=escrow_id_str,
        buyer_id=db_user.id,
        seller_id=product.seller_id,
        product_id=product.id,
        amount=product.price,
    )

    if not success:
        await callback.answer(f"❌ Purchase Failed: {msg}", show_alert=True)
        return

    price_str = TextFormatters.format_currency(product.price, "BDT")

    success_text = (
        f"🔒 **Secure Escrow Order Created!**\n\n"
        f"• **Order ID:** `{order_id_str}`\n"
        f"• **Product:** `{product.title}`\n"
        f"• **Price Secured:** `{price_str}`\n"
        f"• **Escrow Status:** `HELD_IN_ESCROW`\n\n"
        f"Funds have been securely locked. The seller has been notified to deliver the product/service."
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 View My Orders", callback_data="user_orders")],
            [InlineKeyboardButton(text="🔙 Marketplace", callback_data="market_home")],
        ]
    )

    await callback.message.edit_text(success_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "user_orders")
async def cb_user_orders(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays the user's active and past orders (as buyer and seller).
    """
    stmt = select(Order).where(
        (Order.buyer_id == db_user.id) | (Order.seller_id == db_user.id)
    ).order_by(Order.created_at.desc()).limit(5)

    result = await db_session.execute(stmt)
    orders = list(result.scalars().all())

    orders_text = f"📦 **My Escrow Orders**\n\n"

    if not orders:
        orders_text += "No orders found in your history."
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")]])
    else:
        keyboard_buttons = []
        for o in orders:
            role = "Buyer" if o.buyer_id == db_user.id else "Seller"
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"[{role}] Order #{o.order_id} ({o.status.value})", callback_data=f"order_view_{o.id}")
            ])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(orders_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()
  
