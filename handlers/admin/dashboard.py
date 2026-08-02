from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from decimal import Decimal

from database.models.user import User
from database.models.wallet import Wallet
from database.models.deposit import Deposit, DepositStatus
from database.models.escrow import Escrow, EscrowStatus
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "admin_dashboard")
async def cb_admin_dashboard(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays the main Admin Dashboard with platform key metrics and management links.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied. Administrator privileges required.", show_alert=True)
        return

    # Aggregate statistics
    total_users_count = (await db_session.execute(select(func.count(User.id)))).scalar() or 0
    
    total_deposits_sum = (await db_session.execute(
        select(func.sum(Deposit.amount)).where(Deposit.status == DepositStatus.COMPLETED)
    )).scalar() or Decimal("0.00")

    pending_deposits_count = (await db_session.execute(
        select(func.count(Deposit.id)).where(Deposit.status == DepositStatus.PENDING)
    )).scalar() or 0

    active_escrows_count = (await db_session.execute(
        select(func.count(Escrow.id)).where(Escrow.status == EscrowStatus.HELD)
    )).scalar() or 0

    dash_text = (
        f"🔐 **Administrator Control Panel & Dashboard**\n\n"
        f"📊 **Platform Metrics Overview:**\n"
        f"• Total Registered Users: `{total_users_count}`\n"
        f"• Lifetime Completed Deposits: `{TextFormatters.format_currency(total_deposits_sum, 'BDT')}`\n"
        f"• Pending Deposit Approvals: `{pending_deposits_count}`\n"
        f"• Active Escrow Holds: `{active_escrows_count}`\n\n"
        f"Select a management category below:"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"📥 Pending Deposits ({pending_deposits_count})", callback_data="admin_deposits_list"),
                InlineKeyboardButton(text="📤 Withdrawals", callback_data="admin_withdrawals_list"),
            ],
            [
                InlineKeyboardButton(text="🛡️ Escrow Disputes", callback_data="admin_disputes_list"),
                InlineKeyboardButton(text="🎫 Support Tickets", callback_data="admin_tickets_list"),
            ],
            [
                InlineKeyboardButton(text="👥 User Management", callback_data="admin_users_list"),
                InlineKeyboardButton(text="📢 Broadcast Announce", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton(text="🔙 Exit to User Menu", callback_data="main_menu")
            ],
        ]
    )

    await callback.message.edit_text(dash_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()
  
