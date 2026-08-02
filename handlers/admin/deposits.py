from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.user import User
from database.models.deposit import Deposit, DepositStatus
from services.wallet_service import WalletService
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "admin_deposits_list")
async def cb_admin_deposits_list(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays a list of pending deposit requests awaiting admin verification.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    stmt = select(Deposit).where(Deposit.status == DepositStatus.PENDING).order_by(Deposit.created_at.asc()).limit(5)
    result = await db_session.execute(stmt)
    deposits = list(result.scalars().all())

    text = f"📥 **Pending Deposit Requests**\n\n"

    if not deposits:
        text += "No pending deposit requests found."
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
        )
    else:
        keyboard_buttons = []
        for d in deposits:
            amt_str = TextFormatters.format_currency(d.amount, "BDT")
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"[{d.payment_method.value.upper()}] {amt_str} | Trx: {d.transaction_id_claim[:6]}...",
                    callback_data=f"admin_dep_view_{d.id}"
                )
            ])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Dashboard", callback_data="admin_dashboard")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_dep_view_"))
async def cb_admin_deposit_details(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays details of a specific deposit request for review.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    try:
        deposit_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        await callback.answer("Invalid deposit record.", show_alert=True)
        return

    stmt = select(Deposit).where(Deposit.id == deposit_id)
    deposit = (await db_session.execute(stmt)).scalar_one_or_none()

    if not deposit or deposit.status != DepositStatus.PENDING:
        await callback.answer("Deposit request is no longer pending or doesn't exist.", show_alert=True)
        return

    # Fetch depositor user info
    user_stmt = select(User).where(User.id == deposit.user_id)
    depositor = (await db_session.execute(user_stmt)).scalar_one_or_none()
    username = f"@{depositor.username}" if depositor and depositor.username else f"ID: {deposit.user_id}"

    amt_str = TextFormatters.format_currency(deposit.amount, "BDT")

    detail_text = (
        f"🔍 **Deposit Verification Review**\n\n"
        f"• **Deposit ID:** `{deposit.deposit_id}`\n"
        f"• **User:** `{username}`\n"
        f"• **Method:** `{deposit.payment_method.value.upper()}`\n"
        f"• **Amount:** `{amt_str}`\n"
        f"• **Claimed TrxID / Hash:** `{deposit.transaction_id_claim}`\n"
        f"• **Requested At:** `{deposit.created_at.strftime('%d-%m-%Y %H:%M')}`\n\n"
        f"Choose action below:"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve & Credit", callback_data=f"admin_dep_approve_{deposit.id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_dep_reject_{deposit.id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Pending List", callback_data="admin_deposits_list")
            ]
        ]
    )

    await callback.message.edit_text(detail_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_dep_approve_"))
async def cb_admin_deposit_approve(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Approves the deposit, credits user's liquid wallet, and updates status.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    try:
        deposit_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        return

    stmt = select(Deposit).where(Deposit.id == deposit_id)
    deposit = (await db_session.execute(stmt)).scalar_one_or_none()

    if not deposit or deposit.status != DepositStatus.PENDING:
        await callback.answer("Deposit already processed or invalid.", show_alert=True)
        return

    # Update deposit status
    deposit.status = DepositStatus.COMPLETED
    
    # Credit liquid balance to user wallet
    await WalletService.add_balance(db_session, deposit.user_id, deposit.amount)
    await db_session.commit()

    await callback.message.edit_text(
        f"✅ **Deposit Approved Successfully!**\n\n"
        f"• Deposit ID: `{deposit.deposit_id}`\n"
        f"• Credited Amount: `{TextFormatters.format_currency(deposit.amount, 'BDT')}`\n"
        f"• Status: `COMPLETED`",
        reply_markup=InlineKeyboards.get_back_button("admin_deposits_list"),
        parse_mode="Markdown"
    )
    await callback.answer("Deposit approved and funds credited.")
  
