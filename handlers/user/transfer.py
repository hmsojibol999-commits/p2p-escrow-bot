from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from database.models.user import User
from services.wallet_service import WalletService
from services.transaction_service import TransactionService
from services.pin_service import PinService
from keyboards.inline import InlineKeyboards
from utils.states import TransferStates
from utils.validators import InputValidators
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "wallet_transfer")
async def cb_transfer_start(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Initiates the P2P balance transfer flow.
    """
    wallet = await WalletService.get_or_create_wallet(db_session, db_user.id)

    if wallet.balance <= Decimal("0.00"):
        await callback.answer("❌ Your liquid balance is zero. Cannot transfer.", show_alert=True)
        return

    await callback.message.edit_text(
        f"💸 **P2P Wallet Balance Transfer**\n\n"
        f"Available Liquid Balance: `{TextFormatters.format_currency(wallet.balance, 'BDT')}`\n\n"
        f"Please enter the recipient's **Telegram ID** or **Username** (@username):",
        reply_markup=InlineKeyboards.get_back_button("wallet_home"),
        parse_mode="Markdown"
    )
    await callback.state_set if hasattr(callback, 'state_set') else None # Handled via FSM context below
    await callback.answer()


@router.callback_query(F.data == "wallet_transfer") # Alternate router catch
async def start_transfer_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TransferStates.waiting_for_recipient)


# Direct message handler for transfer initiation button or text callback
@router.message(F.text & ~F.text.startswith("/"))
async def handle_transfer_input_router(message: Message, state: FSMContext, db_user: User, db_session: AsyncSession) -> None:
    current_state = await state.get_state()
    if current_state == TransferStates.waiting_for_recipient.state:
        recipient_query = message.text.strip().replace("@", "")
        
        # Search recipient user by telegram_id or username
        recipient = None
        if recipient_query.isdigit():
            recipient = await User.get_by_telegram_id(db_session, int(recipient_query))
        else:
            recipient = await User.get_by_username(db_session, recipient_query)

        if not recipient:
            await message.answer("❌ Recipient user not found in the marketplace database. Please check and enter again:")
            return

        if recipient.id == db_user.id:
            await message.answer("❌ You cannot transfer funds to your own wallet account. Enter another recipient:")
            return

        await state.update_data(recipient_id=recipient.id, recipient_name=recipient.first_name)
        await state.set_state(TransferStates.waiting_for_amount)

        await message.answer(
            f"✅ **Recipient Verified:** `{recipient.first_name}` (ID: {recipient.telegram_id})\n\n"
            f"Now, please enter the amount you wish to transfer:",
            parse_mode="Markdown"
        )
    elif current_state == TransferStates.waiting_for_amount.state:
        is_valid, err_msg, amount = InputValidators.validate_decimal_amount(message.text)
        if not is_valid:
            await message.answer(f"❌ {err_msg}\nPlease enter a valid amount:")
            return

        wallet = await WalletService.get_or_create_wallet(db_session, db_user.id)
        if amount > wallet.balance:
            await message.answer(f"❌ Insufficient liquid balance. Available: `{TextFormatters.format_currency(wallet.balance, 'BDT')}`")
            return

        await state.update_data(amount=str(amount))
        await state.set_state(TransferStates.waiting_for_pin)

        await message.answer(
            f"🔐 **Security PIN Required**\n\n"
            f"Please enter your 4-6 digit Financial PIN to authorize this transfer of `{TextFormatters.format_currency(amount, 'BDT')}`:",
            parse_mode="Markdown"
        )
    elif current_state == TransferStates.waiting_for_pin.state:
        entered_pin = message.text.strip()
        is_valid, pin_msg = await PinService.check_user_pin(db_session, db_user.id, entered_pin)

        if not is_valid:
            await message.answer("❌ Incorrect Financial PIN entered. Please try again:")
            return

        data = await state.get_data()
        recipient_id = data.get("recipient_id")
        recipient_name = data.get("recipient_name")
        amount = Decimal(data.get("amount", "0.00"))

        await state.clear()

        # Execute transfer via WalletService
        success, msg = await WalletService.transfer_funds(db_session, db_user.id, recipient_id, amount)

        if not success:
            await message.answer(
                f"❌ **Transfer Failed**\n\nReason: {msg}",
                reply_markup=InlineKeyboards.get_back_button("wallet_home"),
                parse_mode="Markdown"
            )
            return

        success_text = (
            f"🎉 **P2P Transfer Successful!**\n\n"
            f"• **Recipient:** `{recipient_name}`\n"
            f"• **Amount Transferred:** `{TextFormatters.format_currency(amount, 'BDT')}`\n"
            f"• **Status:** `COMPLETED`\n\n"
            f"Funds have been instantly credited to the recipient's wallet."
        )

        await message.answer(
            success_text,
            reply_markup=InlineKeyboards.get_back_button("wallet_home"),
            parse_mode="Markdown"
      )
      
