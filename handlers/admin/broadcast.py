from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.user import User


router = Router()


class BroadcastStates(StatesGroup):
    """FSM states for handling administrator broadcast campaigns."""
    waiting_for_message = State()


@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast_start(callback: CallbackQuery, db_user: User, state: FSMContext) -> None:
    """
    Initiates the broadcast announcement workflow for administrators.
    """
    if not db_user.is_admin:
        await callback.answer("⛔ Access Denied.", show_alert=True)
        return

    await state.set_state(BroadcastStates.waiting_for_message)

    text = (
        f"📢 **Mass Broadcast Announcement**\n\n"
        f"Send a notification message to all registered marketplace users.\n"
        f"Please enter or forward the announcement message below:"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
    )

    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_dispatch(
    message: Message, state: FSMContext, db_user: User, db_session: AsyncSession, bot: Bot
) -> None:
    """
    Dispatches the broadcast message to all users in the database and reports statistics.
    """
    if not db_user.is_admin:
        await state.clear()
        return

    broadcast_content = message.text or message.caption
    if not broadcast_content:
        await message.answer("❌ Broadcast content cannot be empty. Please enter text or media caption:")
        return

    await state.clear()
    status_msg = await message.answer("⏳ **Broadcasting announcement in progress...** Please wait.")

    # Fetch all registered users
    stmt = select(User.telegram_id)
    result = await db_session.execute(stmt)
    user_ids = [row[0] for row in result.all()]

    success_count = 0
    failed_count = 0

    for uid in user_ids:
        try:
            if message.text:
                await bot.send_message(uid, broadcast_content, parse_mode="Markdown")
            else:
                await message.send_copy(uid)
            success_count += 1
        except Exception:
            failed_count += 1

    report_text = (
        f"📢 **Broadcast Completed Successfully!**\n\n"
        f"• **Total Recipients Targeted:** `{len(user_ids)}`\n"
        f"• **Successfully Delivered:** `{success_count}`\n"
        f"• **Failed / Blocked:** `{failed_count}`"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_dashboard")]]
    )

    await status_msg.edit_text(report_text, reply_markup=markup, parse_mode="Markdown")
  
