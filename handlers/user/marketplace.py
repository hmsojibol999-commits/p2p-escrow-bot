from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.user import User
from database.models.product import Product, ProductStatus
from keyboards.inline import InlineKeyboards
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "market_home")
async def cb_marketplace_home(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Displays the marketplace home page with available active digital products.
    """
    stmt = select(Product).where(Product.status == ProductStatus.ACTIVE).order_by(Product.created_at.desc()).limit(5)
    result = await db_session.execute(stmt)
    products = list(result.scalars().all())

    market_text = (
        f"🛍️ **Decentralized Marketplace - Catalog**\n\n"
        f"Browse secure digital assets and services protected by Escrow.\n"
        f"Select a product below to view details and purchase:"
    )

    keyboard_buttons = []
    if products:
        for p in products:
            price_str = TextFormatters.format_currency(p.price, "BDT")
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"📦 {p.title} ({price_str})", callback_data=f"prod_view_{p.id}")
            ])
    else:
        market_text += "\n\n*No active products available at the moment. Check back soon!*"

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")
    ])

    from aiogram.types import InlineKeyboardMarkup
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(market_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "🛍️ Marketplace")
async def reply_marketplace_home(message: Message, db_session: AsyncSession) -> None:
    """
    Displays the marketplace home page via persistent reply keyboard.
    """
    stmt = select(Product).where(Product.status == ProductStatus.ACTIVE).order_by(Product.created_at.desc()).limit(5)
    result = await db_session.execute(stmt)
    products = list(result.scalars().all())

    market_text = (
        f"🛍️ **Decentralized Marketplace - Catalog**\n\n"
        f"Browse secure digital assets and services protected by Escrow:"
    )

    keyboard_buttons = []
    if products:
        for p in products:
            price_str = TextFormatters.format_currency(p.price, "BDT")
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"📦 {p.title} ({price_str})", callback_data=f"prod_view_{p.id}")
            ])
    else:
        market_text += "\n\n*No active products available right now.*"

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
    ])

    from aiogram.types import InlineKeyboardMarkup
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(market_text, reply_markup=markup, parse_mode="Markdown")


@router.callback_query(F.data.startswith("prod_view_"))
async def cb_view_product_details(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Displays detailed information for a specific product.
    """
    try:
        product_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Invalid product selection.", show_alert=True)
        return

    stmt = select(Product).where(Product.id == product_id)
    product = (await db_session.execute(stmt)).scalar_one_or_none()

    if not product or product.status != ProductStatus.ACTIVE:
        await callback.answer("Product is no longer available or inactive.", show_alert=True)
        return

    price_str = TextFormatters.format_currency(product.price, "BDT")
    desc = product.description or "No description provided."

    detail_text = (
        f"📦 **{product.title}**\n\n"
        f"• **Price:** `{price_str}`\n"
        f"• **Delivery Mode:** `{product.delivery_mode.value.upper()}`\n\n"
        f"📝 **Description:**\n{desc}\n\n"
        f"Click below to initiate a secure Escrow purchase:"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Buy via Escrow Now", callback_data=f"order_buy_{product.id}")],
            [InlineKeyboardButton(text="🔙 Back to Catalog", callback_data="market_home")],
        ]
    )

    await callback.message.edit_text(detail_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()
  
