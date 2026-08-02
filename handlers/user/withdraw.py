from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import secrets

from database.models.user import User
from database.models.deposit import PaymentMethod
from services.wallet_service import WalletService
from services.pin_service import PinService
from keyboards.inline import InlineKeyboards
from utils.states import WithdrawStates
from utils.validators import InputValidators
from utils.formatters import TextFormatters


router = Router()


@router.callback_query(F.data == "wallet_withdraw")
async def cb_withdraw_start(callback: CallbackQuery, db_user: User, db_session: AsyncSession) -> None:
    """
    Initiates the balance withdrawal flow, checking minimum balance and PIN status.
    """
    wallet = await WalletService.get_or_create_wallet(db_session, db_user.id)

    if wallet.balance <= Decimal("0.00"):
        await callback.answer("❌ Your liquid wallet balance is zero. Cannot withdraw.", show_alert=True)
        return

    text = (
        f"📤 **Withdraw Funds**\n\n"
        f"Available Liquid Balance: `{TextFormatters.format_currency(wallet.balance, 'BDT')}`\n\n"
        f"Please select your withdrawal payout method:"
    )

    keyboard = InlineKeyboards.get_deposit_methods_keyboard() # Reusing method layout for payout choice
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("dep_"))
async def cb_withdraw_method_selected(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Captures withdrawal method choice and prompts for amount.
    """
    action = callback.data.split("_")[1]
    method_map = {
        "bkash": PaymentMethod.BKASH,
        "nagad": PaymentMethod.NAGAD,
        "rocket": PaymentMethod.ROCKET,
        "binance": PaymentMethod.BINANCE_PAY,
    }

    if action not in method_map:
        return

    await state.update_data(payout_method=method_map[action])
    await state.set_state(WithdrawStates.waiting_for_amount)

    text = (
        f"📤 **Withdrawal Request**\n\n"
        f"Please enter the amount you wish to withdraw:"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboards.get_back_button("wallet_home"), parse_mode="Markdown")
    await callback.answer()


@router.message(WithdrawStates.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext, db_user: User, db_session: AsyncSession) -> None:
    """
    Validates requested withdrawal amount against available balance.
    """
    is_valid, err_msg, amount = InputValidators.validate_decimal_amount(message.text)
    if not is_valid:
        await message.answer(f"❌ {err_msg}\nPlease enter a valid amount:")
        return

    wallet = await WalletService.get_or_create_wallet(db_session, db_user.id)
    if amount > wallet.balance:
        await message.answer(f"❌ Insufficient liquid balance. You have `{TextFormatters.format_currency(wallet.balance, 'BDT')}` available.")
        return

    await state.update_data(amount=str(amount))
    await state.set_state(WithdrawStates.waiting_for_account)

    await message.answer(
        f"✅ Amount validated: `{amount}`\n\n"
        f"Now, please enter your destination account number (e.g., bKash Personal Number or Binance Pay ID):",
        parse_mode="Markdown"
    )


@router.message(WithdrawStates.waiting_for_account)
async def process_withdraw_account(message: Message, state: FSMContext) -> None:
    """
    Captures destination account number and prompts for financial security PIN.
    """
    account_no = message.text.strip()
    if not account_no or len(account_no) < 5:
        await message.answer("❌ Invalid account number format. Please enter again:")
        return

    await state.update_data(account_number=account_no)
    await state.set_state(WithdrawStates.waiting_for_pin)

    await message.answer(
        f"🔐 **Security PIN Required**\n\n"
        f"Please enter your 4 to 6 digit Financial PIN to authorize this withdrawal:",
        parse_mode="Markdown"
    )


@router.message(WithdrawStates.waiting_for_pin)
async def process_withdraw_pin(
    message: Message, state: FSMContext, db_user: User, db_session: AsyncSession
) -> None:
    """
    Verifies PIN and deducts balance to complete the withdrawal request.
    """
    entered_pin = message.text.strip()
    is_valid, pin_msg = await PinService.check_user_pin(db_session, db_user.id, entered_pin)

    if not is_valid:
        if pin_msg == "PIN_NOT_SET":
            await message.answer("❌ You have not set a financial PIN yet. Please set one in settings.")
        else:
            await message.answer("❌ Incorrect Financial PIN entered. Please try again:")
        return

    data = await state.get_data()
    amount = Decimal(data.get("amount", "0.00"))
    account_number = data.get("account_number")

    # Deduct balance via WalletService
    success, msg = await WalletService.deduct_balance(db_session, db_user.id, amount)
    await state.clear()

    if not success:
        await message.answer(
            f"❌ **Withdrawal Failed**\n\nReason: {msg}",
            reply_markup=InlineKeyboards.get_back_button("wallet_home"),
            parse_mode="Markdown"
        )
        return

    success_text = (
        f"🎉 **Withdrawal Request Submitted Successfully!**\n\n"
        f"• **Amount Deducted:** `{TextFormatters.format_currency(amount, 'BDT')}`\n"
        f"• **Destination Account:** `{account_number}`\n"
        f"• **Status:** `PENDING_DISBURSEMENT`\n\n"
        f"Funds have been deducted from your liquid balance and queued for manual payout."
    )

    await message.answer(
        success_text,
        reply_markup=InlineKeyboards.get_back_button("wallet_home"),
        parse_mode="Markdown"
)
  
