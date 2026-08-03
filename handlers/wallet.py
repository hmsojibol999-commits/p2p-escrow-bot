from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import MIN_DEPOSIT, MIN_WITHDRAW, OWNER_ID

router = Router()

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_trx_id = State()
    waiting_for_number = State()

class WithdrawStates(StatesGroup):
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_number = State()

@router.callback_query(F.data == "menu_wallet")
async def wallet_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        balance = row["balance"] if row else 0.0

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Deposit", callback_data="wallet_deposit"),
         InlineKeyboardButton(text="📤 Withdraw", callback_data="wallet_withdraw")],
        [InlineKeyboardButton(text="📜 Transaction History", callback_data="wallet_history")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(
        f"💼 **Your Wallet**\n\n💰 Balance: ৳{balance:.2f}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    from handlers.start import get_main_menu_keyboard
    await callback.message.edit_text("👋 স্বাগতম! আপনার প্রয়োজনীয় সেবা নিচের মেনু থেকে বেছে নিন:", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- Deposit Flow ---
@router.callback_query(F.data == "wallet_deposit")
async def deposit_start(callback: CallbackQuery, state: FSMContext):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM payment_methods")
        methods = cursor.fetchall()
    
    if not methods:
        # Default fallback methods if admin hasn't added any
        methods_list = ["bKash", "Nagad", "Rocket", "Binance"]
    else:
        methods_list = [m["name"] for m in methods]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=m, callback_data=f"dep_method_{m}")] for m in methods_list
    ] + [[InlineKeyboardButton(text="🔙 Back", callback_data="menu_wallet")]])

    await callback.message.edit_text("💳 পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("dep_method_"))
async def deposit_method_selected(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    await state.update_data(deposit_method=method)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT number FROM payment_methods WHERE name = ?", (method,))
        row = cursor.fetchone()
        pay_number = row["number"] if row and row["number"] else "01XXXXXXXXX (Admin Number)"

    await state.update_data(payment_number=pay_number)
    
    await callback.message.edit_text(
        f"💵 মেথড: **{method}**\n"
        f"টাকা পাঠানোর নম্বর: `{pay_number}`\n\n"
        f"নূন্যতম ডিপোজিট: ৳{MIN_DEPOSIT}\n"
        f"অনুগ্রহ করে পরিমাণ (Amount) লিখুন (শুধু সংখ্যা):",
        parse_mode="Markdown"
    )
    await state.set_state(DepositStates.waiting_for_amount)
    await callback.answer()

@router.message(DepositStates.waiting_for_amount)
async def deposit_get_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount < MIN_DEPOSIT:
            await message.answer(f"⚠️ নূন্যতম ডিপোজিট ৳{MIN_DEPOSIT}। সঠিক পরিমাণ লিখুন:")
            return
    except ValueError:
        await message.answer("⚠️ ভুল পরিমাণ! সঠিক সংখ্যা লিখুন:")
        return

    await state.update_data(deposit_amount=amount)
    data = await state.get_data()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ I Have Sent Money", callback_data="dep_sent_money")]
    ])
    
    await message.answer(
        f"পেমেন্ট সফল করার পর নিচের বাটনে ক্লিক করুন:\n\n"
        f"মেশিন বা সেন্ড মানি করার পর ট্রানজেকশন আইডি প্রদান করতে হবে।",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "dep_sent_money")
async def deposit_sent_money(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 আপনার Transaction ID (TrxID) দিন:")
    await state.set_state(DepositStates.waiting_for_trx_id)
    await callback.answer()

@router.message(DepositStates.waiting_for_trx_id)
async def deposit_get_trx(message: Message, state: FSMContext):
    trx_id = message.text.strip()
    await state.update_data(deposit_trx=trx_id)
    
    await message.answer(
        "🔒 **Privacy Notice:** আপনার নম্বর শুধুমাত্র Payment Verification-এর জন্য নেওয়া হচ্ছে।\n\n"
        "আপনি যে নম্বর থেকে টাকা পাঠিয়েছেন সেই নম্বরটি লিখুন:"
    )
    await state.set_state(DepositStates.waiting_for_number)

@router.message(DepositStates.waiting_for_number)
async def deposit_get_number(message: Message, state: FSMContext):
    sender_number = message.text.strip()
    data = await state.get_data()
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    amount = data["deposit_amount"]
    method = data["deposit_method"]
    trx_id = data["deposit_trx"]
    
    # Mask number (e.g., 017XXXXXX12)
    masked_number = sender_number[:3] + "XXXXXX" + sender_number[-2:] if len(sender_number) >= 5 else "XXXXX"

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO deposit_requests (user_id, amount, method, trx_id, sender_number, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (user_id, amount, method, trx_id, masked_number))
        req_id = cursor.lastrowid
        conn.commit()

    await message.answer("✅ আপনার ডিপোজিট রিকোয়েস্ট সফলভাবে সাবমিট হয়েছে। এডমিন ভেরিফাই করার পর ব্যালেন্স যোগ করা হবে।")

    # Notify Owner/Admin
    if OWNER_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Approve", callback_data=f"adm_dep_app_{req_id}"),
             InlineKeyboardButton(text="Reject", callback_data=f"adm_dep_rej_{req_id}")]
        ])
        try:
            await message.bot.send_message(
                OWNER_ID,
                f"📥 **New Deposit Request #{req_id}**\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"🔗 Username: @{username}\n"
                f"💵 Amount: ৳{amount}\n"
                f"💳 Method: {method}\n"
                f"🆔 TrxID: `{trx_id}`\n"
                f"📞 Sender: `{masked_number}`",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except Exception:
            pass

# --- Withdraw Flow ---
@router.callback_query(F.data == "wallet_withdraw")
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (callback.from_user.id,))
        row = cursor.fetchone()
        balance = row["balance"] if row else 0.0

    if balance < MIN_WITHDRAW:
        await callback.answer(f"⚠️ নূন্যতম উইথড্র ব্যালেন্স ৳{MIN_WITHDRAW} হতে হবে। আপনার আছে ৳{balance}", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="bKash", callback_data="w_method_bKash"),
         InlineKeyboardButton(text="Nagad", callback_data="w_method_Nagad")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="menu_wallet")]
    ])
    await callback.message.edit_text("📤 উইথড্র করার জন্য পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("w_method_"))
async def withdraw_method(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    await state.update_data(withdraw_method=method)
    await callback.message.edit_text(f"📤 মেথড: **{method}**\n\nআপনার উইথড্র পরিমাণ লিখুন (শুধু সংখ্যা):", parse_mode="Markdown")
    await state.set_state(WithdrawStates.waiting_for_amount)
    await callback.answer()

@router.message(WithdrawStates.waiting_for_amount)
async def withdraw_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (message.from_user.id,))
            balance = cursor.fetchone()["balance"]
        
        if amount < MIN_WITHDRAW or amount > balance:
            await message.answer(f"⚠️ ভুল পরিমাণ! নূন্যতম ৳{MIN_WITHDRAW} অথবা আপনার বর্তমান ব্যালেন্স (৳{balance}) এর বেশি উইথড্র করা যাবে না:")
            return
    except ValueError:
        await message.answer("⚠️ সঠিক সংখ্যা লিখুন:")
        return

    await state.update_data(withdraw_amount=amount)
    await message.answer("📞 আপনার ব্যক্তিগত পেমেন্ট নম্বরটি দিন (যে নম্বরে টাকা নিতে চান):")
    await state.set_state(WithdrawStates.waiting_for_number)

@router.message(WithdrawStates.waiting_for_number)
async def withdraw_number(message: Message, state: FSMContext):
    number = message.text.strip()
    data = await state.get_data()
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    amount = data["withdraw_amount"]
    method = data["withdraw_method"]

    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Deduct balance immediately upon request
        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        cursor.execute("""
            INSERT INTO withdraw_requests (user_id, amount, method, user_number, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (user_id, amount, method, number))
        req_id = cursor.lastrowid
        conn.commit()

    await message.answer("✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে সাবমিট হয়েছে।")

    if OWNER_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Approve", callback_data=f"adm_wd_app_{req_id}"),
             InlineKeyboardButton(text="Reject", callback_data=f"adm_wd_rej_{req_id}")]
        ])
        try:
            await message.bot.send_message(
                OWNER_ID,
                f"📤 **New Withdraw Request #{req_id}**\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"🔗 Username: @{username}\n"
                f"💵 Amount: ৳{amount}\n"
                f"💳 Method: {method}\n"
                f"📞 Number: `{number}`",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        except Exception:
            pass

@router.callback_query(F.data == "wallet_history")
async def wallet_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT type, amount, description, created_at FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
        rows = cursor.fetchall()

    if not rows:
        await callback.answer("📜 কোনো ট্রানজেকশন হিস্ট্রি নেই।", show_alert=True)
        return

    text = "📜 **Last 10 Transactions:**\n\n"
    for r in rows:
        text += f"• {r['type'].upper()}: ৳{r['amount']} - {r['description']} ({r['created_at']})\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="menu_wallet")]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    
