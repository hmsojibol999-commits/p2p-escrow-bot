from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.user import User
from database.models.escrow import Escrow, EscrowStatus
from services.escrow_service import EscrowService
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "admin_disputes_list")
async def cb_admin_disputes_list(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays active escrow disputes requiring admin intervention.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    stmt = select(Escrow).where(Escrow.status == EscrowStatus.DISPUTED).order_by(Escrow.created_at.desc()).limit(5)
    result = await db_session.execute(stmt)
    disputes = list(result.scalars().all())

    text = f"🛡️ **Active Escrow Disputes & Claims**\n\n"

    if not disputes:
        text += "No active escrow disputes found. All orders running smoothly."
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
        )
    else:
        keyboard_buttons = []
        for d in disputes:
            amt_str = TextFormatters.format_currency(d.amount, "BDT")
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"Escrow #{d.escrow_id} | {amt_str} (DISPUTED)",
                    callback_data=f"admin_disp_view_{d.id}"
                )
            ])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Dashboard", callback_data="admin_dashboard")])
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_disp_view_"))
async def cb_admin_dispute_details(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays details of a disputed escrow for final resolution by admin.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    try:
        escrow_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        await callback.answer("Invalid escrow record.", show_alert=True)
        return

    stmt = select(Escrow).where(Escrow.id == escrow_id)
    escrow = (await db_session.execute(stmt)).scalar_one_or_none()

    if not escrow or escrow.status != EscrowStatus.DISPUTED:
        await callback.answer("Dispute record not found or already resolved.", show_alert=True)
        return

    amt_str = TextFormatters.format_currency(escrow.amount, "BDT")

    detail_text = (
        f"⚖️ **Escrow Dispute Arbitration Panel**\n\n"
        f"• **Escrow ID:** `{escrow.escrow_id}`\n"
        f"• **Buyer ID:** `{escrow.buyer_id}`\n"
        f"• **Seller ID:** `{escrow.seller_id}`\n"
        f"• **Escrow Amount:** `{amt_str}`\n"
        f"• **Status:** `DISPUTED`\n\n"
        f"Review evidence and choose a final binding resolution:"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refund Buyer", callback_data=f"admin_disp_refund_{escrow.id}"),
                InlineKeyboardButton(text="💸 Release to Seller", callback_data=f"admin_disp_release_{escrow.id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 Disputes List", callback_data="admin_disputes_list")
            ]
        ]
    )

    await callback.message.edit_text(detail_text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_disp_refund_"))
async def cb_admin_dispute_refund_buyer(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Resolves dispute by refunding the held escrow amount back to the buyer.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    try:
        escrow_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError):
        return

    stmt = select(Escrow).where(Escrow.id == escrow_id)
    escrow = (await db_session.execute(stmt)).scalar_one_or_none()

    if not escrow or escrow.status != EscrowStatus.DISPUTED:
        await callback.answer("Escrow not in disputed state.", show_alert=True)
        return

    success, msg = await EscrowService.refund_escrow_to_buyer(db_session, escrow.id)

    if not success:
        await callback.answer(f"❌ Failed: {msg}", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ **Dispute Resolved: Refunded to Buyer**\n\n"
        f"• Escrow ID: `{escrow.escrow_id}`\n"
        f"• Amount Refunded: `{TextFormatters.format_currency(escrow.amount, 'BDT')}`\n"
        f"• Status: `REFUNDED_TO_BUYER`",
        reply_markup=InlineKeyboards.get_back_button("admin_disputes_list"),
        parse_mode="Markdown"
    )
    await callback.answer("Dispute resolved successfully.")
                              
