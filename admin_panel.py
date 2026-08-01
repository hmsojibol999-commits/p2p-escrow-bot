from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_connection

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_payment_details = State()

# ⚙️ MAIN ADMIN PANEL
@admin_router.message(F.text == "⚙️ Admin Panel")
async def open_admin_panel(message: types.Message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (message.from_user.id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row["role"] != "admin":
        await message.answer("❌ **আপনার এই সেকশনে প্রবেশের অনুমতি নেই!**")
        return

    text = (
        "⚙️ **Admin Control Panel**\n\n"
        "বটের যাবতীয় সেটিংস ও ডাটা কন্ট্রোল করতে নিচের অপশন বেছে নিন:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📁 Manage Categories", callback_data="adm_manage_cats"),
            InlineKeyboardButton(text="💳 Payment Methods", callback_data="adm_manage_payments")
        ],
        [
            InlineKeyboardButton(text="📦 Pending Products", callback_data="adm_pending_prods"),
            InlineKeyboardButton(text="🏪 Seller Applications", callback_data="adm_seller_apps")
        ],
        [InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# 💳 PAYMENT METHODS MANAGEMENT
@admin_router.callback_query(F.data == "adm_manage_payments")
async def manage_payments(callback: types.CallbackQuery):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment_methods")
    methods = cursor.fetchall()
    conn.close()

    text = "💳 **Payment Methods Setup**\n\nআপনার বর্তমান পেমেন্ট নম্বরসমূহ:\n\n"
    if methods:
        for m in methods:
            text += f"• **{m['method_name'].upper()}:** `{m['account_details']}`\n"
    else:
        text += "⚠️ কোনো নম্বর সেট করা নেই।\n"

    text += "\nনম্বর যোগ/আপডেট করতে নিচের বাটনে চাপ দিন:"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💗 bKash Set", callback_data="set_pay_bkash"),
            InlineKeyboardButton(text="🧡 Nagad Set", callback_data="set_pay_nagad")
        ],
        [
            InlineKeyboardButton(text="🚀 Rocket Set", callback_data="set_pay_rocket"),
            InlineKeyboardButton(text="🟡 Binance Set", callback_data="set_pay_binance")
        ],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="adm_back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@admin_router.callback_query(F.data.startswith("set_pay_"))
async def prompt_payment_details(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[2]
    await state.update_data(target_method=method)
    await state.set_state(AdminStates.waiting_for_payment_details)

    await callback.message.answer(
        f"📝 **{method.upper()} নম্বর/আইডিটি লিখুন:**\n\n"
        f"উদাহরণ: `01700000000 (Personal)` অথবা `Binance Pay ID: 12345678`\n\n"
        "ক্যানসেল করতে /cancel লিখুন।"
    )

@admin_router.message(AdminStates.waiting_for_payment_details)
async def save_payment_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    method = data.get("target_method")
    details = message.text

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payment_methods (method_name, account_details)
        VALUES (?, ?)
        ON CONFLICT(method_name) DO UPDATE SET account_details=excluded.account_details
    """, (method, details))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ **{method.upper()} তথ্য সফলভাবে সেভ করা হয়েছে!**\n\n`{details}`")

# 📁 CATEGORY MANAGEMENT
@admin_router.callback_query(F.data == "adm_manage_cats")
async def manage_categories(callback: types.CallbackQuery):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    cats = cursor.fetchall()
    conn.close()

    text = "📁 **Category Management**\n\nবর্তমান ক্যাটাগরি সমূহ:\n"
    if cats:
        for c in cats:
            text += f"• {c['name']}\n"
    else:
        text += "⚠️ কোনো ক্যাটাগরি তৈরি করা হয়নি।\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add New Category", callback_data="adm_add_cat")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="adm_back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@admin_router.callback_query(F.data == "adm_add_cat")
async def prompt_add_category(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_category_name)
    await callback.message.answer("📝 **নতুন ক্যাটাগরির নাম লিখুন:**\n\nউদাহরণ: `Accounts` বা `Software`")

@admin_router.message(AdminStates.waiting_for_category_name)
async def save_category(message: types.Message, state: FSMContext):
    cat_name = message.text.strip()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
        conn.commit()
        await message.answer(f"✅ **ক্যাটাগরি `{cat_name}` সফলভাবে যুক্ত করা হয়েছে!**")
    except Exception as e:
        await message.answer("❌ **এরর:** ক্যাটাগরি ইতিমধ্যেই থাকতে পারে!")
    finally:
        conn.close()
        await state.clear()
        
