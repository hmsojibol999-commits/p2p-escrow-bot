from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from database.models.user import User
from database.models.deposit import PaymentMethod
from services.gateways.manual_pay import ManualPaymentGateway
from services.gateways.crypto_pay import CryptoPaymentGateway
from keyboards.inline import InlineKeyboards
from utils.states import DepositStates
from utils.validators import InputValidators
from utils.formatters import TextFormatters
import secrets


router = Router()


@router.callback_query(F.data == "wallet_deposit")
async def cb_deposit_menu(callback: CallbackQuery) -> None:
    """
    Displays the payment gateway selection menu for depositing funds.
    """
    text = (
        f"➕ **Deposit Funds to Wallet**\n\n"
        f"Please select your preferred local or crypto payment gateway below:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboards.get_deposit_methods_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dep_"))
async def cb_select_gateway(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handles gateway selection and prompts user to enter deposit amount.
    """
    action = callback.data.split("_")[1]
    
    method_map = {
        "bkash": (PaymentMethod.BKASH, "bKash (Manual)"),
        "nagad": (PaymentMethod.NAGAD, "Nagad (Manual)"),
        "rocket": (PaymentMethod.ROCKET, "Rocket (Manual)"),
        "binance": (PaymentMethod.BINANCE_PAY, "Binance Pay / Crypto"),
    }

    if action not in method_map:
        await callback.answer("Invalid payment gateway selected.", show_alert=True)
        return

    pay_enum, pay_name = method_map[action]
    await state.update_data(payment_method=pay_enum, gateway_name=pay_name)
    await state.set_state(DepositStates.waiting_for_amount)

    currency = "USDT" if pay_enum == PaymentMethod.BINANCE_PAY else "BDT"

    text = (
        f"💳 **Gateway Selected:** `{pay_name}`\n\n"
        f"Please enter the amount you wish to deposit in **{currency}**:\n"
        f"(Example: `1000` or `500.50`)"
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboards.get_back_button("wallet_deposit"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext) -> None:
    """
    Validates deposit amount and proceeds to request Transaction ID/Hash.
    """
    is_valid, err_msg, amount = InputValidators.validate_decimal_amount(message.text)
    if not is_valid:
        await message.answer(f"❌ {err_msg}\nPlease enter a valid amount:")
        return

    await state.update_data(amount=str(amount))
    await state.set_state(DepositStates.waiting_for_trx_id)

    data = await state.get_data()
    gateway_name = data.get("gateway_name", "Gateway")

    prompt_text = (
        f"✅ **Amount Recorded:** `{amount}`\n\n"
        f"Now, please provide the **Transaction ID (TrxID)** or **Binance Pay Order ID / Hash** for verification:"
    )

    await message.answer(prompt_text, parse_mode="Markdown")


@router.message(DepositStates.waiting_for_trx_id)
async def process_deposit_trx_id(
    message: Message, state: FSMContext, db_user: User, db_session: AsyncSession
) -> None:
    """
    Receives TrxID, validates uniqueness, and submits deposit request to DB.
    """
    trx_id = message.text.strip()
    if not trx_id or len(trx_id) < 4:
        await message.answer("❌ Invalid Transaction ID. Please enter a valid TrxID or Hash:")
        return

    data = await state.get_data()
    payment_method = data.get("payment_method")
    amount = Decimal(data.get("amount", "0.00"))
    deposit_id = f"DEP-{secrets.token_hex(4).upper()}"

    # Route submission based on method category
    if payment_method in [PaymentMethod.BKASH, PaymentMethod.NAGAD, PaymentMethod.ROCKET]:
        success, msg, _ = await ManualPaymentGateway.submit_deposit_request(
            session=db_session,
            deposit_id=deposit_id,
            user_id=db_user.id,
            payment_method=payment_method,
            amount=amount,
            transaction_id_claim=trx_id,
        )
    else:
        success, msg, _ = await CryptoPaymentGateway.submit_crypto_deposit(
            session=db_session,
            deposit_id=deposit_id,
            user_id=db_user.id,
            payment_method=payment_method,
            amount=amount,
            transaction_hash_claim=trx_id,
        )

    await state.clear()

    if not success:
        await message.answer(
            f"❌ **Deposit Submission Failed**\n\nReason: {msg}",
            reply_markup=InlineKeyboards.get_back_button("wallet_home"),
            parse_mode="Markdown"
        )
        return

    formatted_amt = TextFormatters.format_currency(amount, "USDT" if payment_method == PaymentMethod.BINANCE_PAY else "BDT")

    success_text = (
        f"🎉 **Deposit Request Submitted Successfully!**\n\n"
        f"• **Deposit ID:** `{deposit_id}`\n"
        f"• **Amount:** `{formatted_amt}`\n"
        f"• **TrxID / Hash:** `{trx_id}`\n"
        f"• **Status:** `PENDING_REVIEW`\n\n"
        f"Your deposit is currently under review by our admin team. Balance will be credited upon confirmation."
    )

    await message.answer(
        success_text,
        reply_markup=InlineKeyboards.get_back_button("wallet_home"),
        parse_mode="Markdown"
  )
  
