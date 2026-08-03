import logging
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from config import MIN_DEPOSIT, MIN_WITHDRAW, OWNER_ID
from database import Database

logger = logging.getLogger(__name__)
router = Router()
db = Database()

def get_utc_now() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def mask_number(number: str) -> str:
    """Masks a sender or receiver number for privacy, showing first 3 and last 2 digits."""
    if not number or len(number) < 6:
        return "****"
    return number[:3] + "X" * (len(number) - 5) + number[-2:]

# ================= FSM States =================
class DepositStates(StatesGroup):
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_trx_id = State()
    waiting_for_sender_number = State()

class WithdrawStates(StatesGroup):
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_receive_number = State()

# ================= Keyboards =================
def get_wallet_menu_keyboard() -> InlineKeyboardMarkup:
    """Generates the wallet main menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Deposit", callback_data="wallet_deposit"),
            InlineKeyboardButton(text="📤 Withdraw", callback_data="wallet_withdraw")
        ],
        [
            InlineKeyboardButton(text="📜 Transaction History", callback_data="wallet_transactions")
        ],
        [
            InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="menu_main")
        ]
    ])

def get_back_to_wallet_keyboard() -> InlineKeyboardMarkup:
    """Generates a back button to return to wallet menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Wallet", callback_data="menu_wallet")]
    ])

# ================= Wallet Menu Handlers =================
@router.callback_query(F.data == "menu_wallet")
async def show_wallet_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Displays the wallet dashboard with current balances and stats."""
    await state.clear()
    user_id = callback.from_user.id

    try:
        await db.connect()
        wallet = await db.fetchone(
            "SELECT balance, total_deposit, total_withdraw, total_spent FROM wallets WHERE telegram_id = ?;",
            (user_id,)
        )

        if not wallet:
            await db.execute(
                "INSERT INTO wallets (telegram_id, balance, total_deposit, total_withdraw, total_spent) VALUES (?, 0.0, 0.0, 0.0, 0.0);",
                (user_id,)
            )
            balance, total_deposit, total_withdraw, total_spent = 0.0, 0.0, 0.0, 0.0
        else:
            balance = wallet["balance"]
            total_deposit = wallet["total_deposit"]
            total_withdraw = wallet["total_withdraw"]
            total_spent = wallet["total_spent"]

        text = (
            f"💼 <b>আপনার ওয়ালেট ড্যাশবোর্ড</b>\n\n"
            f"💰 বর্তমান ব্যালেন্স: <b>৳{balance:.2f}</b>\n"
            f"📥 মোট ডিপোজিট: ৳{total_deposit:.2f}\n"
            f"📤 মোট উইথড্র: ৳{total_withdraw:.2f}\n"
            f"🛒 মোট খরচ: ৳{total_spent:.2f}\n\n"
            f"নিচের অপশনগুলো থেকে আপনার প্রয়োজনীয় সেবাটি বেছে নিন:"
        )

        try:
            await callback.message.edit_text(text, reply_markup=get_wallet_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=get_wallet_menu_keyboard())
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing wallet menu for user {user_id}: {e}")
        await callback.answer("⚠️ ওয়ালেট লোড করতে সমস্যা হয়েছে।", show_alert=True)

# ================= Deposit Flow =================
@router.callback_query(F.data == "wallet_deposit")
async def start_deposit(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the deposit flow by loading active payment methods."""
    try:
        await db.connect()
        methods = await db.fetchall(
            "SELECT id, name, number FROM payment_methods WHERE enabled = 1 ORDER BY display_order ASC;"
        )

        if not methods:
            await callback.answer("⚠️ বর্তমানে কোনো ডিপোজিট মেথড উপলব্ধ নেই।", show_alert=True)
            return

        keyboard_buttons = []
        for m in methods:
            keyboard_buttons.append([InlineKeyboardButton(text=m["name"], callback_data=f"dep_method_{m['name']}")])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Back to Wallet", callback_data="menu_wallet")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        text = "📥 <b>ডিপোজিট মেথড নির্বাচন করুন</b>\n\nঅনুগ্রহ করে নিচে দেওয়া মাধ্যমগুলোর মধ্য থেকে একটি সিলেক্ট করুন:"
        
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await state.set_state(DepositStates.waiting_for_method)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting deposit flow: {e}")
        await callback.answer("⚠️ ত্রুটি ঘটেছে। আবার চেষ্টা করুন।", show_alert=True)

@router.callback_query(DepositStates.waiting_for_method, F.data.startswith("dep_method_"))
async def process_deposit_method(callback: CallbackQuery, state: FSMContext) -> None:
    """Processes selected deposit method and asks for amount."""
    method_name = callback.data.replace("dep_method_", "", 1)
    
    await state.update_data(payment_method=method_name)
    await state.set_state(DepositStates.waiting_for_amount)

    text = (
        f"💳 সিলেক্টেড মেথড: <b>{method_name}</b>\n\n"
        f"আপনি কত টাকা ডিপোজিট করতে চান?\n"
        f"ℹ️ <b>সর্বনিম্ন ডিপোজিট: ৳{MIN_DEPOSIT}</b>\n\n"
        f"দয়া করে শুধু টাকার পরিমাণটি (সংখ্যায়) লিখুন:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_back_to_wallet_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_back_to_wallet_keyboard())
    await callback.answer()

@router.message(DepositStates.waiting_for_amount, F.text)
async def process_deposit_amount(message: Message, state: FSMContext) -> None:
    """Validates deposit amount and displays admin payment account info."""
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("⚠️ ভুল ফরম্যাট! দয়া করে সঠিক সংখ্যা লিখুন (যেমন: 500)।", reply_markup=get_back_to_wallet_keyboard())
        return

    if amount < MIN_DEPOSIT:
        await message.answer(f"⚠️ সর্বনিম্ন ডিপোজিট পরিমাণ ৳{MIN_DEPOSIT}! এর চেয়ে কম ডিপোজিট করা যাবে না।", reply_markup=get_back_to_wallet_keyboard())
        return

    await state.update_data(amount=amount)

    data = await state.get_data()
    method_name = data.get("payment_method")

    try:
        await db.connect()
        method_row = await db.fetchone(
            "SELECT number FROM payment_methods WHERE name = ? AND enabled = 1;",
            (method_name,)
        )

        if not method_row:
            await message.answer("⚠️ পেমেন্ট মেথডটি পাওয়া যায়নি অথবা বন্ধ রয়েছে।", reply_markup=get_back_to_wallet_keyboard())
            await state.clear()
            return

        payment_number = method_row["number"]
        await state.update_data(payment_number=payment_number)
        await state.set_state(DepositStates.waiting_for_trx_id)

        instruction_text = (
            f"📌 <b>পেমেন্ট নির্দেশিকা</b>\n\n"
            f"মেথড: <b>{method_name}</b>\n"
            f"একাউন্ট নম্বর: <code>{payment_number}</code> (Send Money / Cash In)\n"
            f"পরিমাণ: <b>৳{amount}</b>\n\n"
            f"সঠিক নম্বরে টাকা পাঠানোর পর নিচের বাটনে ক্লিক করুন এবং আপনার Transaction ID (TrxID) দিন।"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ আমি টাকা পাঠিয়ে ফেলেছি", callback_data="dep_money_sent")],
            [InlineKeyboardButton(text="❌ বাতিল করুন", callback_data="menu_wallet")]
        ])

        await message.answer(instruction_text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error processing deposit amount: {e}")
        await message.answer("⚠️ একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।", reply_markup=get_back_to_wallet_keyboard())

@router.callback_query(DepositStates.waiting_for_trx_id, F.data == "dep_money_sent")
async def prompt_deposit_trx_id(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompts user to enter transaction ID after money is sent."""
    text = "✍️ দয়া করে আপনার পেমেন্টের <b>Transaction ID (TrxID)</b> টি এখানে লিখুন:"
    try:
        await callback.message.edit_text(text, reply_markup=get_back_to_wallet_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_back_to_wallet_keyboard())
    await callback.answer()

@router.message(DepositStates.waiting_for_trx_id, F.text)
async def process_deposit_trx_id(message: Message, state: FSMContext) -> None:
    """Captures Transaction ID and asks for sender number with privacy notice."""
    trx_id = message.text.strip()
    if len(trx_id) < 3:
        await message.answer("⚠️ সঠিক Transaction ID দিন।", reply_markup=get_back_to_wallet_keyboard())
        return

    await state.update_data(transaction_id=trx_id)
    await state.set_state(DepositStates.waiting_for_sender_number)

    privacy_text = (
        f"🔒 <b>গোপনীয়তা ও নিরাপত্তা নোটিশ</b>\n\n"
        f"আপনি যে নম্বর থেকে টাকা পাঠিয়েছেন (Sender Number) সেই নম্বরটি দিন।\n"
        f"এই নম্বর শুধুমাত্র Payment Verification-এর জন্য ব্যবহার করা হবে। আপনার ব্যক্তিগত তথ্য সম্পূর্ণ নিরাপদ থাকবে।\n"
        f"Admin সম্পূর্ণ নম্বর দেখতে পাবে না, শুধুমাত্র সিকিউরড মাস্কড নম্বর দেখতে পাবে।\n\n"
        f"দয়া করে আপনার সেন্ডার নম্বরটি লিখুন:"
    )

    await message.answer(privacy_text, reply_markup=get_back_to_wallet_keyboard())

@router.message(DepositStates.waiting_for_sender_number, F.text)
async def process_deposit_sender_number(message: Message, state: FSMContext) -> None:
    """Validates sender number, saves request, and notifies Owner Admin."""
    sender_number = message.text.strip()
    if len(sender_number) < 6:
        await message.answer("⚠️ সঠিক সেন্ডার নম্বর দিন।", reply_markup=get_back_to_wallet_keyboard())
        return

    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    amount = data.get("amount")
    method_name = data.get("payment_method")
    payment_number = data.get("payment_number")
    trx_id = data.get("transaction_id")
    now = get_utc_now()

    try:
        await db.connect()
        cursor = await db.execute(
            """
            INSERT INTO deposit_requests 
            (telegram_id, amount, payment_method, payment_number, sender_number, transaction_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?);
            """,
            (user_id, amount, method_name, payment_number, sender_number, trx_id, now)
        )
        request_id = cursor.lastrowid
        await state.clear()

        await message.answer(
            f"✅ <b>ডিপোজিট রিকোয়েস্ট সফলভাবে জমা হয়েছে!</b>\n\n"
            f"রিসেপ্ট আইডি: #{request_id}\n"
            f"পরিমাণ: ৳{amount}\n"
            f"মেথড: {method_name}\n"
            f"TrxID: {trx_id}\n\n"
            f"অ্যাডমিন আপনার পেমেন্ট ভেরিফাই করার পর ব্যালেন্স যোগ করা হবে। অনুগ্রহ করে অপেক্ষা করুন।",
            reply_markup=get_wallet_menu_keyboard()
        )

        # Notify Owner Admin with masked sender number
        masked_sender = mask_number(sender_number)
        admin_text = (
            f"🔔 <b>নতুন ডিপোজিট রিকোয়েস্ট!</b> (#REQ{request_id})\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"🔗 Username: @{username}\n"
            f"💰 Amount: <b>৳{amount}</b>\n"
            f"💳 Method: {method_name}\n"
            f"🏷️ TrxID: <code>{trx_id}</code>\n"
            f"📱 Sender No (Masked): <code>{masked_sender}</code>\n"
            f"⏱️ Time: {now}"
        )

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_dep_approve_{request_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_dep_reject_{request_id}")
            ]
        ])

        try:
            await message.bot.send_message(chat_id=OWNER_ID, text=admin_text, reply_markup=admin_keyboard)
        except Exception as admin_err:
            logger.error(f"Failed to notify owner admin about deposit {request_id}: {admin_err}")

    except Exception as e:
        logger.error(f"Error saving deposit request for user {user_id}: {e}")
        await message.answer("⚠️ একটি অভ্যন্তরীণ ত্রুটি ঘটেছে। দয়া করে পরে আবার চেষ্টা করুন।", reply_markup=get_wallet_menu_keyboard())
        await state.clear()

# ================= Withdraw Flow =================
@router.callback_query(F.data == "wallet_withdraw")
async def start_withdraw(callback: CallbackQuery, state: FSMContext) -> None:
    """Starts the withdraw flow by checking balance and loading payment methods."""
    user_id = callback.from_user.id
    try:
        await db.connect()
        wallet = await db.fetchone("SELECT balance FROM wallets WHERE telegram_id = ?;", (user_id,))
        balance = wallet["balance"] if wallet else 0.0

        if balance < MIN_WITHDRAW:
            await callback.answer(f"⚠️ পর্যাপ্ত ব্যালেন্স নেই! সর্বনিম্ন উইথড্র ৳{MIN_WITHDRAW} (আপনার বর্তমান ব্যালেন্স: ৳{balance:.2f})", show_alert=True)
            return

        methods = await db.fetchall(
            "SELECT id, name FROM payment_methods WHERE enabled = 1 ORDER BY display_order ASC;"
        )

        if not methods:
            await callback.answer("⚠️ বর্তমানে কোনো উইথড্র মেথড উপলব্ধ নেই।", show_alert=True)
            return

        keyboard_buttons = []
        for m in methods:
            keyboard_buttons.append([InlineKeyboardButton(text=m["name"], callback_data=f"wit_method_{m['name']}")])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Back to Wallet", callback_data="menu_wallet")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        text = (
            f"📤 <b>উইথড্র মেথড নির্বাচন করুন</b>\n\n"
            f"আপনার বর্তমান ব্যালেন্স: <b>৳{balance:.2f}</b>\n\n"
            f"অনুগ্রহ করে মাধ্যম সিলেক্ট করুন:"
        )

        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)

        await state.update_data(current_balance=balance)
        await state.set_state(WithdrawStates.waiting_for_method)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error starting withdraw flow: {e}")
        await callback.answer("⚠️ ত্রুটি ঘটেছে। আবার চেষ্টা করুন።", show_alert=True)

@router.callback_query(WithdrawStates.waiting_for_method, F.data.startswith("wit_method_"))
async def process_withdraw_method(callback: CallbackQuery, state: FSMContext) -> None:
    """Processes selected withdraw method and asks for amount."""
    method_name = callback.data.replace("wit_method_", "", 1)
    await state.update_data(payment_method=method_name)
    await state.set_state(WithdrawStates.waiting_for_amount)

    data = await state.get_data()
    balance = data.get("current_balance", 0.0)

    text = (
        f"💳 সিলেক্টেড মেথড: <b>{method_name}</b>\n"
        f"💰 উপলব্ধ ব্যালেন্স: <b>৳{balance:.2f}</b>\n\n"
        f"আপনি কত টাকা উইথড্র করতে চান?\n"
        f"ℹ️ <b>সর্বনিম্ন উইথড্র: ৳{MIN_WITHDRAW}</b>\n\n"
        f"দয়া করে পরিমাণটি (সংখ্যায়) লিখুন:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_back_to_wallet_keyboard())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=get_back_to_wallet_keyboard())
    await callback.answer()

@router.message(WithdrawStates.waiting_for_amount, F.text)
async def process_withdraw_amount(message: Message, state: FSMContext) -> None:
    """Validates withdraw amount against balance and limits."""
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("⚠️ ভুল ফরম্যাট! সঠিক সংখ্যা লিখুন।", reply_markup=get_back_to_wallet_keyboard())
        return

    data = await state.get_data()
    balance = data.get("current_balance", 0.0)

    if amount < MIN_WITHDRAW:
        await message.answer(f"⚠️ সর্বনিম্ন উইথড্র পরিমাণ ৳{MIN_WITHDRAW}!", reply_markup=get_back_to_wallet_keyboard())
        return

    if amount > balance:
        await message.answer(f"⚠️ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই! (বর্তমান ব্যালেন্স: ৳{balance:.2f})", reply_markup=get_back_to_wallet_keyboard())
        return

    await state.update_data(amount=amount)
    await state.set_state(WithdrawStates.waiting_for_receive_number)

    text = "📥 আপনি যে নম্বরে টাকা গ্রহণ করতে চান (Receive Number) সেটি লিখুন:"
    await message.answer(text, reply_markup=get_back_to_wallet_keyboard())

@router.message(WithdrawStates.waiting_for_receive_number, F.text)
async def process_withdraw_receive_number(message: Message, state: FSMContext) -> None:
    """Captures receive number, saves withdraw request (without deducting balance yet), and notifies Owner Admin."""
    receive_number = message.text.strip()
    if len(receive_number) < 6:
        await message.answer("⚠️ সঠিক রিসিভ নম্বর দিন।", reply_markup=get_back_to_wallet_keyboard())
        return

    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    amount = data.get("amount")
    method_name = data.get("payment_method")
    now = get_utc_now()

    try:
        await db.connect()
        # Save request with status 'pending'. Balance is NOT deducted at request time per rules.
        cursor = await db.execute(
            """
            INSERT INTO withdraw_requests 
            (telegram_id, amount, payment_method, receive_number, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?);
            """,
            (user_id, amount, method_name, receive_number, now)
        )
        request_id = cursor.lastrowid
        await state.clear()

        await message.answer(
            f"✅ <b>উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে!</b>\n\n"
            f"রিসেপ্ট আইডি: #{request_id}\n"
            f"পরিমাণ: ৳{amount}\n"
            f"মেথড: {method_name}\n"
            f"নম্বর: {receive_number}\n\n"
            f"অ্যাডমিন অনুমোদন করার পর আপনার অ্যাকাউন্টে পেমেন্ট পৌঁছে দেওয়া হবে।",
            reply_markup=get_wallet_menu_keyboard()
        )

        # Notify Owner Admin
        admin_text = (
            f"🔔 <b>নতুন উইথড্র রিকোয়েস্ট!</b> (#WIT{request_id})\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"🔗 Username: @{username}\n"
            f"💰 Amount: <b>৳{amount}</b>\n"
            f"💳 Method: {method_name}\n"
            f"📱 Receive No: <code>{receive_number}</code>\n"
            f"⏱️ Time: {now}"
        )

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_wit_approve_{request_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_wit_reject_{request_id}")
            ]
        ])

        try:
            await message.bot.send_message(chat_id=OWNER_ID, text=admin_text, reply_markup=admin_keyboard)
        except Exception as admin_err:
