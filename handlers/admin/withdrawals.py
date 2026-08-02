from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.user import User
from database.models.deposit import Deposit, DepositStatus, PaymentMethod
from services.wallet_service import WalletService
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "admin_withdrawals_list")
async def cb_admin_withdrawals_list(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays a list of pending withdrawal requests awaiting admin payout.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    # In our DB design, withdrawals can share the Deposit table with a negative/payout flag or a separate status.
    # Here we query deposits/withdrawals where status is PENDING and type matches payout.
    stmt = select(Deposit).where(
        (Deposit.status == DepositStatus.PENDING) & (Deposit.amount < 0)
    ).order_by(Deposit.created_at.asc()).limit(5)
    
    result = await db_session.execute(stmt)
    withdrawals = list(result.scalars().all())

    text = f"📤 **Pending Payout Withdrawals**\n\n"

    if not withdrawals:
        text += "No pending withdrawal requests found."
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
        )
    else:
        keyboard_buttons = []
        for w in withdrawals:
            abs_amt = abs(w.amount)
            amt_str = TextFormatters.format_currency(abs_amt, "BDT")
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"[{w.payment_method.value.upper()}] {amt_str} | Acc: {w.transaction_id_claim[:6]}...",
                    callback_data=f"admin_wd_view_{w.id}"
                )
            ])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Dashboard", callback_data="admin_dashboard")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_wd_view_"))
async def cb_admin_withdrawal_details(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays details of a specific withdrawal request for manual payout.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    try:
        wd_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        await callback.answer("Invalid withdrawal record.", show_alert=True)
        return

    stmt = select(Deposit).where(Deposit.id == wd_id)
    withdrawal = (await db_session.execute(stmt)).scalar_one_or_none()

    if not withdrawal or withdrawal.status != DepositStatus.PENDING:
        await callback.answer("Withdrawal request is no longer pending.", show_alert=True)
        return

    user_stmt = select(User).where(User.id == withdrawal.user_id)
    requester = (await db_session.execute(user_stmt)).scalar_one_or_none()
    username = f"@{requester.username}" if requester and requester.username else f"ID: {withdrawal.user_id}"

    abs_amt = abs(withdrawal.amount)
    amt_str = TextFormatters.format_currency(abs_amt, "BDT")

    detail_text = (
        f"🔍 **Withdrawal Payout Review**\n\n"
        f"• **Request ID:** `{withdrawal.deposit_id}`\n"
        f"• **User:** `{username}`\n"
        f"• **Method:** `{withdrawal.payment_method.value.upper()}`\n"
        f"• **Payout Amount:** `{amt_str}`\n"
        f"• **Destination Account:** `{withdrawal.transaction_id_claim}`\n"
        f"• **Requested At:** `{withdrawal.created_at.strftime('%d-%m-%Y %H:%M')}`\n\n"
        f"Mark as disbursed or reject to refund user:"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Mark Paid (Disburse)", callback_data=f"admin_wd_approve_{withdrawal.id}"),
                InlineKeyboardButton(text="❌ Reject & Refund", callback_data=f"admin_wd_reject_{withdrawal.id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Withdrawals List", callback_data="admin_withdrawals_list")
            ]
        ]
    )

    await callback.message.edit_text(detail_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_wd_approve_"))
async def cb_admin_withdrawal_approve(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Marks withdrawal request as completed/paid out.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    try:
        wd_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        return

    stmt = select(Deposit).where(Deposit.id == wd_id)
    withdrawal = (await db_session.execute(stmt)).scalar_one_or_none()

    if not withdrawal or withdrawal.status != DepositStatus.PENDING:
        await callback.answer("Record already processed.", show_alert=True)
        return

    withdrawal.status = DepositStatus.COMPLETED
    await db_session.commit()

    await callback.message.edit_text(
        f"✅ **Withdrawal Payout Completed!**\n\n"
        f"• Request ID: `{withdrawal.deposit_id}`\n"
        f"• Status: `DISBURSED`",
        reply_markup=InlineKeyboards.get_back_button("admin_withdrawals_list"),
        parse_mode="Markdown"
    )
    await callback.answer("Withdrawal marked as paid.")
  
