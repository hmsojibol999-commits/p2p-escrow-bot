import asyncio
import os
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ⚙️ CONFIGURATION
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Apnar Telegram Numeric ID

USDT_RATE = 125.0  # 1 USDT = 125 BDT
BINANCE_PAY_ID = "110549937"
BKASH_NUMBER = "01833878871"
NAGAD_NUMBER = "01833878871"
ROCKET_NUMBER = "01833878871"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🗄️ DATABASE SETUP
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method TEXT,
            amount REAL,
            trx_or_username TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method TEXT,
            amount REAL,
            account_number TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

def get_user_balance(user_id, first_name="", username=""):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, first_name, username, balance) VALUES (?, ?, ?, ?)",
                       (user_id, first_name, username, 0.0))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return balance

def update_user_balance(user_id, amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# 🧠 FSM STATES
class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_trx = State()

class WithdrawState(StatesGroup):
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_account = State()

# 🔘 MAIN MENU KEYBOARD
def main_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Buy Products")],
            [KeyboardButton(text="👤 My Profile"), KeyboardButton(text="💳 Deposit")],
            [KeyboardButton(text="📤 Withdraw"), KeyboardButton(text="👨‍💻 Support")]
        ],
        resize_keyboard=True
    )

# 🚀 START COMMAND
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user = message.from_user
    get_user_balance(user.id, user.first_name, user.username or "N/A")
    welcome_text = (
        f"👋 **Ji {user.first_name}! P2P Escrow Bot-e shagotom.**\n\n"
        "Nirapode ID kenabecha o wallet manage korte nicher option-gulo use korun:"
    )
    await message.answer(welcome_text, reply_markup=main_reply_keyboard(), parse_mode="Markdown")

# 👤 PROFILE HANDLER
@dp.message(F.text == "👤 My Profile")
async def profile_handler(message: types.Message):
    user = message.from_user
    balance = get_user_balance(user.id, user.first_name, user.username or "N/A")
    text = (
        f"👤 **Apnar Profile & Wallet**\n\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"👤 **Name:** {user.first_name}\n"
        f"💰 **Balance:** {balance:.2f} BDT\n"
    )
    await message.answer(text, parse_mode="Markdown")

# 💳 DEPOSIT FLOW
@dp.message(F.text == "💳 Deposit")
async def deposit_start(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💗 bKash", callback_data="dep_bkash"), InlineKeyboardButton(text="🧡 Nagad", callback_data="dep_nagad")],
        [InlineKeyboardButton(text="💜 Rocket", callback_data="dep_rocket")],
        [InlineKeyboardButton(text="🟡 Binance (USDT)", callback_data="dep_binance")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_action")]
    ])
    await message.answer("💳 **Select Payment Method:**", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("dep_"))
async def deposit_method_selected(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(deposit_method=method)
    await state.set_state(DepositState.waiting_for_amount)
    
    cancel_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_action")]
    ])
    
    if method == "binance":
        text = "🟡 **Binance — Enter Amount**\n\nEnter deposit amount in **USDT**:"
    else:
        text = f"📱 **{method.capitalize()}**\n\nEnter deposit amount in **BDT**:\n*(Minimum: 10 BDT)*"
        
    await callback.message.edit_text(text, reply_markup=cancel_btn, parse_mode="Markdown")
    await callback.answer()

@dp.message(DepositState.waiting_for_amount)
async def process_dep_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Anugraha kore shothik shongkhya likhun (e.g. 10 athoba 2).")
        return

    user_data = await state.get_data()
    method = user_data.get("deposit_method")
    await state.update_data(deposit_amount=amount)
    await state.set_state(DepositState.waiting_for_trx)

    cancel_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_action")]
    ])

    if method == "binance":
        bdt_equiv = amount * USDT_RATE
        text = (
            f"🟡 **Binance Deposit**\n\n"
            f"Send: **{amount:.4f} USDT**\n"
            f"≈ **{bdt_equiv:.2f} BDT** (Rate: 1 USDT = {USDT_RATE} BDT)\n\n"
            f"Pay to Binance Pay ID:\n`{BINANCE_PAY_ID}`\n\n"
            f"Taka pathanor por apnar **Binance Username** ba **Pay ID** pathan:"
        )
    else:
        num = BKASH_NUMBER if method == "bkash" else NAGAD_NUMBER if method == "nagad" else ROCKET_NUMBER
        text = (
            f"📱 **{method.capitalize()} Deposit**\n\n"
            f"Send **{amount:.2f} BDT** (Send Money) to:\n`{num}`\n\n"
            f"Taka pathanor por **Transaction ID (TrxID)** ekhane pathan:"
        )

    await message.answer(text, reply_markup=cancel_btn, parse_mode="Markdown")

@dp.message(DepositState.waiting_for_trx)
async def process_dep_trx(message: types.Message, state: FSMContext):
    trx_input = message.text.strip()
    user_data = await state.get_data()
    method = user_data.get("deposit_method")
    amount = user_data.get("deposit_amount")
    
    bdt_amount = amount * USDT_RATE if method == "binance" else amount

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO deposits (user_id, method, amount, trx_or_username) VALUES (?, ?, ?, ?)",
                   (message.from_user.id, method, bdt_amount, trx_input))
    dep_id = cursor.lastrowid
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ **Request Jama Hoyeche!**\n\nAdmin verify kore 1-2 minute-er moddhe balance add kore dibe.", parse_mode="Markdown")

    # 📩 Notify Admin with Approve/Reject Buttons
    admin_btn = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"appdep_{dep_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"rejdep_{dep_id}")
        ]
    ])
    admin_text = (
        f"📥 **NEW DEPOSIT REQUEST (#DEP{dep_id})**\n\n"
        f"👤 **User:** {message.from_user.first_name} (`{message.from_user.id}`)\n"
        f"💳 **Method:** {method.upper()}\n"
        f"💰 **Amount:** {bdt_amount:.2f} BDT\n"
        f"🆔 **Trx/User:** `{trx_input}`"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_btn, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to notify admin: {e}")

# 📤 WITHDRAW FLOW
@dp.message(F.text == "📤 Withdraw")
async def withdraw_start(message: types.Message, state: FSMContext):
    balance = get_user_balance(message.from_user.id)
    if balance <= 0:
        await message.answer("⚠️ Apnar wallet-e kono balance nei!")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💗 bKash", callback_data="wd_bkash"), InlineKeyboardButton(text="🧡 Nagad", callback_data="wd_nagad")],
        [InlineKeyboardButton(text="🟡 Binance (USDT)", callback_data="wd_binance")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_action")]
    ])
    await message.answer(f"📤 **Withdraw Request**\n\nAvailable Balance: **{balance:.2f} BDT**\n\nSelect Payout Method:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("wd_"))
async def withdraw_method_selected(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(withdraw_method=method)
    await state.set_state(WithdrawState.waiting_for_amount)
    
    await callback.message.edit_text(f"📤 **{method.upper()} Withdraw**\n\nKoto BDT withdraw korte chan likhun:")
    await callback.answer()

@dp.message(WithdrawState.waiting_for_amount)
async def process_wd_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        balance = get_user_balance(message.from_user.id)
        if amount <= 0 or amount > balance:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Anugraha kore shothik amount likhun ja apnar balance-er shoman ba kom.")
        return

    await state.update_data(withdraw_amount=amount)
    await state.set_state(WithdrawState.waiting_for_account)
    
    user_data = await state.get_data()
    method = user_data.get("withdraw_method")
    
    label = "Binance Pay ID / USDT TRC20 Address" if method == "binance" else f"{method.capitalize()} Mobile Number"
    await message.answer(f"📝 Apnar **{label}** pathan:")

@dp.message(WithdrawState.waiting_for_account)
async def process_wd_account(message: types.Message, state: FSMContext):
    account_no = message.text.strip()
    user_data = await state.get_data()
    method = user_data.get("withdraw_method")
    amount = user_data.get("withdraw_amount")
    
    # Balance Hold / Deduct
    update_user_balance(message.from_user.id, -amount)

    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO withdrawals (user_id, method, amount, account_number) VALUES (?, ?, ?, ?)",
                   (message.from_user.id, method, amount, account_no))
    wd_id = cursor.lastrowid
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ **Withdraw Request Submitted!**\n\nAdmin verify kore apnar account-e taka pathiye dibe.", parse_mode="Markdown")

    # 📩 Admin Notification
    admin_btn = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Complete Payout", callback_data=f"appwd_{wd_id}"),
            InlineKeyboardButton(text="❌ Reject & Refund", callback_data=f"rejwd_{wd_id}")
        ]
    ])
    admin_text = (
        f"📤 **NEW WITHDRAW REQUEST (#WD{wd_id})**\n\n"
        f"👤 **User:** {message.from_user.first_name} (`{message.from_user.id}`)\n"
        f"💳 **Method:** {method.upper()}\n"
        f"💰 **Amount:** {amount:.2f} BDT\n"
        f"📱 **Account:** `{account_no}`"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_btn, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to notify admin: {e}")

# 👑 ADMIN CALLBACK HANDLERS
@dp.callback_query(F.data.startswith("appdep_"))
async def approve_deposit(callback: types.CallbackQuery):
    dep_id = callback.data.split("_")[1]
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM deposits WHERE id = ?", (dep_id,))
    row = cursor.fetchone()
    
    if row and row[2] == "Pending":
        user_id, amount, _ = row
        cursor.execute("UPDATE deposits SET status = 'Approved' WHERE id = ?", (dep_id,))
        conn.commit()
        conn.close()
        
        update_user_balance(user_id, amount)
        
        await callback.message.edit_text(callback.message.text + "\n\n🟢 **STATUS: APPROVED**")
        try:
            await bot.send_message(user_id, f"🎉 **Deposit Approved!**\n\nApnar wallet-e **{amount:.2f} BDT** balance add kora hoyeche.", parse_mode="Markdown")
        except:
            pass
    else:
        conn.close()
        await callback.answer("Already processed!")

@dp.callback_query(F.data.startswith("rejdep_"))
async def reject_deposit(callback: types.CallbackQuery):
    dep_id = callback.data.split("_")[1]
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status FROM deposits WHERE id = ?", (dep_id,))
    row = cursor.fetchone()
    
    if row and row[1] == "Pending":
        user_id = row[0]
        cursor.execute("UPDATE deposits SET status = 'Rejected' WHERE id = ?", (dep_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text(callback.message.text + "\n\n🔴 **STATUS: REJECTED**")
        try:
            await bot.send_message(user_id, "❌ Apnar deposit request-ti reject kora hoyeche. Shothik TrxID die abar chesta korun.")
        except:
            pass
    else:
        conn.close()
        await callback.answer("Already processed!")

@dp.callback_query(F.data.startswith("appwd_"))
async def approve_withdraw(callback: types.CallbackQuery):
    wd_id = callback.data.split("_")[1]
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM withdrawals WHERE id = ?", (wd_id,))
    row = cursor.fetchone()
    
    if row and row[2] == "Pending":
        user_id, amount, _ = row
        cursor.execute("UPDATE withdrawals SET status = 'Completed' WHERE id = ?", (wd_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text(callback.message.text + "\n\n🟢 **STATUS: COMPLETED**")
        try:
            await bot.send_message(user_id, f"🎉 **Withdraw Successful!**\n\nApnar **{amount:.2f} BDT** payout complete kora hoyeche.", parse_mode="Markdown")
        except:
            pass
    else:
        conn.close()
        await callback.answer("Already processed!")

@dp.callback_query(F.data.startswith("rejwd_"))
async def reject_withdraw(callback: types.CallbackQuery):
    wd_id = callback.data.split("_")[1]
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM withdrawals WHERE id = ?", (wd_id,))
    row = cursor.fetchone()
    
    if row and row[2] == "Pending":
        user_id, amount, _ = row
        cursor.execute("UPDATE withdrawals SET status = 'Rejected' WHERE id = ?", (wd_id,))
        conn.commit()
        conn.close()
        
        # Refund Balance
        update_user_balance(user_id, amount)
        
        await callback.message.edit_text(callback.message.text + "\n\n🔴 **STATUS: REJECTED & REFUNDED**")
        try:
            await bot.send_message(user_id, f"❌ Apnar withdraw request-ti reject kora hoyeche. **{amount:.2f} BDT** wallet-e refund dewa hoyeche.")
        except:
            pass
    else:
        conn.close()
        await callback.answer("Already processed!")

# ❌ CANCEL ACTION
@dp.callback_query(F.data == "cancel_action")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Action cancelled.")
    await callback.answer()

# 🌐 RENDER HEALTH CHECK SERVER
async def handle_health_check(request):
    return web.Response(text="Part 1: Core Wallet Engine is Alive and Running!")

async def main():
    init_db()
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("Bot is starting Part 1 Engine...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
