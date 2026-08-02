from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from services.wallet_service import WalletService
from services.transaction_service import TransactionService
from keyboards.inline import InlineKeyboards
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "wallet_home")
async def cb_wallet_dashboard(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays the user's comprehensive financial wallet dashboard.
    """
    wallet = await WalletService.get_or_create_wallet(db_session, db_user.id)
    summary = await TransactionService.get_user_financial_summary(db_session, db_user.id)

    liquid_str = TextFormatters.format_currency(wallet.balance, "BDT")
    escrow_str = TextFormatters.format_currency(wallet.escrow_balance, "BDT")
    total_dep_str = TextFormatters.format_currency(summary["total_deposited"], "BDT")
    total_earned_str = TextFormatters.format_currency(summary["total_sales_income"], "BDT")

    wallet_text = (
        f"💼 **My Financial Wallet Dashboard**\n\n"
        f"• **Liquid Balance:** `{liquid_str}`\n"
        f"• **Escrow Hold Balance:** `{escrow_str}`\n\n"
        f"📊 **Lifetime Statistics:**\n"
        f"• Total Deposited: `{total_dep_str}`\n"
        f"• Total Sales Income: `{total_earned_str}`\n"
        f"• Wallet Status: `{wallet.status.value.upper()}`\n\n"
        f"Select an action below:"
    )

    await callback.message.edit_text(
        wallet_text,
        reply_markup=InlineKeyboards.get_wallet_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(F.text == "💼 My Wallet")
async def reply_wallet_dashboard(message: Message, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays the wallet dashboard via persistent reply keyboard.
    """
    wallet = await WalletService.get_or_create_wallet(db_session, db_user.id)
    summary = await TransactionService.get_user_financial_summary(db_session, db_user.id)

    liquid_str = TextFormatters.format_currency(wallet.balance, "BDT")
    escrow_str = TextFormatters.format_currency(wallet.escrow_balance, "BDT")

    wallet_text = (
        f"💼 **My Financial Wallet Dashboard**\n\n"
        f"• **Liquid Balance:** `{liquid_str}`\n"
        f"• **Escrow Hold Balance:** `{escrow_str}`\n\n"
        f"Choose an option below:"
    )

    await message.answer(
        wallet_text,
        reply_markup=InlineKeyboards.get_wallet_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "wallet_history")
async def cb_wallet_history(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays recent transaction ledger history for the user.
    """
    transactions, total_count = await TransactionService.get_user_transactions(
        db_session, db_user.id, limit=5
    )

    if not transactions:
        history_text = "📜 **Transaction Ledger History**\n\nNo financial transactions recorded yet."
    else:
        history_text = f"📜 **Recent Transaction History** (Total: {total_count})\n\n"
        for tx in transactions:
            sign = "+" if tx.transaction_type.value in ["deposit", "sale", "transfer_in", "refund"] else "-"
            amt_str = TextFormatters.format_currency(tx.amount, "BDT")
            history_text += f"• `{tx.created_at.strftime('%d-%m-%Y %H:%M')}` | {tx.transaction_type.value.upper()}\n  {sign}**{amt_str}** | Status: *{tx.status.value}*\n\n"

    await callback.message.edit_text(
        history_text,
        reply_markup=InlineKeyboards.get_back_button("wallet_home"),
        parse_mode="Markdown"
    )
    await callback.answer()
  
