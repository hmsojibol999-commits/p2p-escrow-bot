from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_connection

wallet_router = Router()

class WalletStates(StatesGroup):
    waiting_for_deposit_amount = State()
    waiting_for_deposit_trxid = State()

@wallet_router.callback_query(F.data == "wallet_deposit")
async def start_deposit(callback: types.CallbackQuery):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment_methods WHERE status = 'active'")
    methods = cursor.fetchall()
    conn.close()

    if not methods:
        await callback.answer("⚠️ Admin payment method set koreni!", show_alert=True)
        return

    text = "💳 **Deposit Method Select Korun:**\n\nNicher je kono ekti method select korun:"
    kb = []
    for m in methods:
        kb.append([InlineKeyboardButton(text=f"➔ {m['method_name'].upper()}", callback_data=f"dep_select_{m['method_name']}")])
    
    kb.append([InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@wallet_router.callback_query(F.data.startswith("dep_select_"))
async def prompt_deposit_amount(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT account_details FROM payment_methods WHERE method_name = ?", (method,))
    row = cursor.fetchone()
    conn.close()

    details = row["account_details"] if row else "N/A"
    await state.update_data(dep_method=method, dep_details=details)
    await state.set_state(WalletStates.waiting_for_deposit_amount)

    text = (
        f"📲 **{method.upper()} Deposit Details**\n\n"
        f"📍 Send Money / Payment To:\n`{details}`\n\n"
        "💵 **Koto Taka Deposit korben?**\nAmount-ti Shudhu Number-e Likhun (e.g. `500`):"
    )
    await callback.message.answer(text, parse_mode="Markdown")

@wallet_router.message(WalletStates.waiting_for_deposit_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError()
        
        await state.update_data(dep_amount=amount)
        await state.set_state(WalletStates.waiting_for_deposit_trxid)
        
        await message.answer("📝 **Payment-er Transaction ID (TrxID) ba Proof Text Likhun:**\n\nExample: `9J34KS829L`")
    except ValueError:
        await message.answer("❌ **Sothik Amount Likhun!** (e.g. 100, 500, 1000)")

@wallet_router.message(WalletStates.waiting_for_deposit_trxid)
async def process_deposit_trxid(message: types.Message, state: FSMContext):
    trxid = message.text.strip()
    data = await state.get_data()
    method = data.get("dep_method")
    amount = data.get("dep_amount")
    user = message.from_user

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, type, method, amount, account_info, status)
        VALUES (?, 'deposit', ?, ?, ?, 'pending')
    """, (user.id, method, amount, trxid))
    conn.commit()
    conn.close()

    await state.clear()

    await message.answer(
        f"✅ **Deposit Request Submitted!**\n\n"
        f"💳 **Method:** {method.upper()}\n"
        f"💵 **Amount:** {amount} BDT\n"
        f"🧾 **TrxID:** `{trxid}`\n\n"
        "⏳ Admin Verifying Korar Por Apnar Balance-e Taka Add Hoye Jabe.",
        parse_mode="Markdown"
    )
  
