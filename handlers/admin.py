from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import OWNER_ID, SUPPORT_ADMIN_ID
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class AdminStates(StatesGroup):
    add_category = State()
    add_product_title = State()
    add_product_price = State()
    add_product_stock = State()
    wallet_adjust = State()
    broadcast = State()

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id != SUPPORT_ADMIN_ID:
        return

    is_owner = (user_id == OWNER_ID)
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="📂 Categories", callback_data="adm_categories"),
         InlineKeyboardButton(text="📦 Products", callback_data="adm_products")],
        [InlineKeyboardButton(text="📥 Deposits", callback_data="adm_deposits"),
         InlineKeyboardButton(text="📤 Withdraws", callback_data="adm_withdraws")]
    ]
    
    if is_owner:
        keyboard_buttons.append([InlineKeyboardButton(text="💰 Wallet Control", callback_data="adm_wallet_ctrl"),
                                 InlineKeyboardButton(text="📢 Broadcast", callback_data="adm_broadcast")])
        keyboard_buttons.append([InlineKeyboardButton(text="⚙️ Settings", callback_data="adm_settings")])

    await message.answer("🛠 **Admin Dashboard**", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons), parse_mode="Markdown")

# --- Deposit / Withdraw Approval Callbacks ---
@router.callback_query(F.data.startswith("adm_dep_app_"))
async def adm_dep_approve(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("⚠️ আপনার এই অনুমতি নেই!", show_alert=True)
        return
    
    req_id = int(callback.data.split("_")[3])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deposit_requests WHERE id = ? AND status = 'pending'", (req_id,))
        req = cursor.fetchone()
        if not req:
            await callback.answer("⚠️ রিকোয়েস্টটি ইতিমধ্যে প্রসেস করা হয়েছে।", show_alert=True)
            return

        user_id = req["user_id"]
        amount = req["amount"]

        cursor.execute("UPDATE deposit_requests SET status = 'approved' WHERE id = ?", (req_id,))
        cursor.execute("UPDATE wallets SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (?, 'deposit', ?, ?)
        """, (user_id, amount, f"Deposit Approved (TrxID: {req['trx_id']})"))
        conn.commit()

    await callback.message.edit_text(callback.message.text + "\n\n✅ **Approved**")
    try:
        await callback.bot.send_message(user_id, f"✅ আপনার ৳{amount} ডিপোজিট রিকোয়েস্ট অনুমোদিত হয়েছে এবং ব্যালেন্স যোগ হয়েছে!")
    except Exception:
        pass
    await callback.answer()

@router.callback_query(F.data.startswith("adm_dep_rej_"))
async def adm_dep_reject(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("⚠️ আপনার এই অনুমতি নেই!", show_alert=True)
        return
    
    req_id = int(callback.data.split("_")[3])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE deposit_requests SET status = 'rejected' WHERE id = ?", (req_id,))
        conn.commit()

    await callback.message.edit_text(callback.message.text + "\n\n❌ **Rejected**")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_wd_app_"))
async def adm_wd_approve(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("⚠️ আপনার এই অনুমতি নেই!", show_alert=True)
        return
    
    req_id = int(callback.data.split("_")[3])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE withdraw_requests SET status = 'approved' WHERE id = ?", (req_id,))
        conn.commit()

    await callback.message.edit_text(callback.message.text + "\n\n✅ **Withdraw Approved**")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_wd_rej_"))
async def adm_wd_reject(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("⚠️ আপনার এই অনুমতি নেই!", show_alert=True)
        return
    
    req_id = int(callback.data.split("_")[3])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM withdraw_requests WHERE id = ?", (req_id,))
        req = cursor.fetchone()
        if req and req["status"] == 'pending':
            # Refund balance if rejected
            cursor.execute("UPDATE wallets SET balance = balance + ? WHERE user_id = ?", (req["amount"], req["user_id"]))
            cursor.execute("UPDATE withdraw_requests SET status = 'rejected' WHERE id = ?", (req_id,))
            conn.commit()

    await callback.message.edit_text(callback.message.text + "\n\n❌ **Withdraw Rejected & Refunded**")
    await callback.answer()

# --- Categories Management ---
@router.callback_query(F.data == "adm_categories")
async def adm_categories(callback: CallbackQuery):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        cats = cursor.fetchall()

    text = "📂 **Categories Management:**\n\n"
    buttons = [[InlineKeyboardButton(text="➕ Add Category", callback_data="adm_add_cat")]]
    for c in cats:
        buttons.append([InlineKeyboardButton(text=c["name"], callback_data=f"none"),
                        InlineKeyboardButton(text="❌ Delete", callback_data=f"adm_del_cat_{c['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_panel_back")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "adm_add_cat")
async def adm_add_cat_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍️ নতুন ক্যাটাগরির নাম লিখুন:")
    await state.set_state(AdminStates.add_category)
    await callback.answer()

@router.message(AdminStates.add_category)
async def adm_save_cat(message: Message, state: FSMContext):
    cat_name = message.text.strip()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
            conn.commit()
            await message.answer("✅ ক্যাটাগরি সফলভাবে যোগ করা হয়েছে।")
        except Exception:
            await message.answer("⚠️ এই নামে ইতিমধ্যে ক্যাটাগরি রয়েছে।")
    await state.clear()

@router.callback_query(F.data.startswith("adm_del_cat_"))
async def adm_del_cat(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[3])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
    await callback.answer("✅ ক্যাটাগরি ডিলিট করা হয়েছে।", show_alert=True)
    await adm_categories(callback)

# --- Broadcast Feature ---
@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != OWNER_ID:
        return
    await callback.message.edit_text("📢 সকল ইউজারের কাছে পাঠানোর জন্য ম্যাসেজটি লিখুন:")
    await state.set_state(AdminStates.broadcast)
    await callback.answer()

@router.message(AdminStates.broadcast)
async def adm_send_broadcast(message: Message, state: FSMContext):
    text = message.text
    await state.clear()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

    count = 0
    for u in users:
        try:
            await message.bot.send_message(u["user_id"], text)
            count += 1
        except Exception:
            pass

    await message.answer(f"✅ ব্রডকাস্ট সফল! মোট {count} জন ইউজারের কাছে পাঠানো হয়েছে।")

@router.callback_query(F.data == "admin_panel_back")
async def admin_panel_back(callback: CallbackQuery):
    await admin_panel(callback.message)
    await callback.answer()
  
