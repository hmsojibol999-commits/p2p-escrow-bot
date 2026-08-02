from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from database.models.user import User
from database.models.support import SupportTicket, TicketStatus
from utils.states import SupportTicketStates
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "support_home")
async def cb_support_home(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Displays user's support tickets and option to open a new ticket.
    """
    stmt = select(SupportTicket).where(SupportTicket.user_id == db_user.id).order_by(SupportTicket.created_at.desc()).limit(5)
    result = await db_session.execute(stmt)
    tickets = list(result.scalars().all())

    text = (
        f"🎫 **Customer Support & Help Desk**\n\n"
        f"Need assistance with a deposit, order, or escrow? Open a support ticket below:"
    )

    keyboard_buttons = [
        [InlineKeyboardButton(text="➕ Open New Support Ticket", callback_data="support_create")]
    ]

    for t in tickets:
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"Ticket #{t.ticket_id} ({t.status.value.upper()})", callback_data=f"ticket_view_{t.id}")
        ])

    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "support_create")
async def cb_support_create(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Initiates support ticket creation FSM flow.
    """
    await state.set_state(SupportTicketStates.waiting_for_subject)
    text = (
        f"🎫 **Open Support Ticket**\n\n"
        f"Please enter a short subject or title for your issue:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Support", callback_data="support_home")]])
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.message(SupportTicketStates.waiting_for_subject)
async def process_ticket_subject(message: Message, state: FSMContext) -> None:
    """
    Captures ticket subject and prompts for detailed message.
    """
    subject = message.text.strip()
    if not subject or len(subject) < 3:
        await message.answer("❌ Subject is too short. Please enter a valid subject:")
        return

    await state.update_data(subject=subject)
    await state.set_state(SupportTicketStates.waiting_for_message)

    await message.answer(
        f"✅ **Subject Recorded:** `{subject}`\n\n"
        f"Now, please describe your issue in detail:",
        parse_mode="Markdown"
    )


@router.message(SupportTicketStates.waiting_for_message)
async def process_ticket_message(
    message: Message, state: FSMContext, db_user: User, db_session: AsyncSession
) -> None:
    """
    Captures description, creates ticket record in DB, and clears FSM.
    """
    body = message.text.strip()
    if not body or len(body) < 5:
        await message.answer("❌ Message description is too short. Please provide more detail:")
        return

    data = await state.get_data()
    subject = data.get("subject")
    ticket_id_str = f"TICK-{secrets.token_hex(4).upper()}"

    ticket = SupportTicket(
        ticket_id=ticket_id_str,
        user_id=db_user.id,
        subject=subject,
        message=body,
        status=TicketStatus.OPEN,
    )
    db_session.add(ticket)
    await db_session.commit()
    await state.clear()

    success_text = (
        f"🎉 **Support Ticket Created Successfully!**\n\n"
        f"• **Ticket ID:** `{ticket_id_str}`\n"
        f"• **Subject:** `{subject}`\n"
        f"• **Status:** `OPEN`\n\n"
        f"Our support staff has been notified and will reply shortly."
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🎫 View Support Tickets", callback_data="support_home")]]
    )

    await message.answer(success_text, reply_markup=markup, parse_mode="Markdown")
  
