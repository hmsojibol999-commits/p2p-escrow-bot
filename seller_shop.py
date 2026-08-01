from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_connection

seller_router = Router()

class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title = State()
    waiting_for_price = State()
    waiting_for_stock_data = State()

# --- SELLER DASHBOARD ---
@seller_router.callback_query(F.data == "seller_add_product")
async def start_add_product(callback: types.CallbackQuery, state: FSMContext):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    cats = cursor.fetchall()
    conn.close()

    if not cats:
        await callback.answer("⚠️ কোনো ক্যাটাগরি পাওয়া যায়নি! এডমিনকে ক্যাটাগরি যুক্ত করতে বলুন।", show_alert=True)
        return

    kb = []
    for c in cats:
        kb.append([InlineKeyboardButton(text=f"📁 {c['name']}", callback_data=f"sel_cat_{c['id']}")])
    kb.append([InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")])

    await state.set_state(AddProductStates.waiting_for_category)
    await callback.message.edit_text(
        "📦 **প্রোডাক্টের ক্যাটাগরি সিলেক্ট করুন:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )

@seller_router.callback_query(F.data.startswith("sel_cat_"))
async def process_cat_selection(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[2])
    await state.update_data(cat_id=cat_id)
    await state.set_state(AddProductStates.waiting_for_title)

    await callback.message.answer(
        "📝 **প্রোডাক্টের টাইটেল/নাম লিখুন:**\n\n*(যেমন: Gmail Aged 2023 / Premium Netflix Account)*"
    )

@seller_router.message(AddProductStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(product_title=title)
    await state.set_state(AddProductStates.waiting_for_price)

    await message.answer("💵 **প্রতিটি অ্যাকাউন্টের দাম (BDT) কত লিখুন:**\n\n*(যেমন: 50, 150, 300)*")

@seller_router.message(AddProductStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError()
        
        await state.update_data(product_price=price)
        await state.set_state(AddProductStates.waiting_for_stock_data)

        await message.answer(
            "📂 **প্রোডাক্টের স্টক ডেটা (Email:Pass) আপলোড করুন:**\n\n"
            "প্রতি লাইনে ১টি করে অ্যাকাউন্ট লিখুন।\n"
            "উদাহরণ:\n"
            "`user1@gmail.com:pass123`\n"
            "`user2@gmail.com:pass456`",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("❌ **সঠিক মূল্য লিখুন!** (উদাহরণ: 50)")

@seller_router.message(AddProductStates.waiting_for_stock_data)
async def process_stock_data(message: types.Message, state: FSMContext):
    raw_data = message.text.strip().split("\n")
    stock_items = [line.strip() for line in raw_data if line.strip()]

    if not stock_items:
        await message.answer("❌ কোনো স্টক ডেটা পাওয়া যায়নি! সঠিকভাবে Email:Pass লিখুন।")
        return

    data = await state.get_data()
    cat_id = data.get("cat_id")
    title = data.get("product_title")
    price = data.get("product_price")
    seller_id = message.from_user.id

    conn = get_connection()
    cursor = conn.cursor()

    # Create Product
    cursor.execute("""
        INSERT INTO products (seller_id, category_id, title, price, description)
        VALUES (?, ?, ?, ?, 'Automated Delivery Stock')
    """, (seller_id, cat_id, title, price))
    
    product_id = cursor.lastrowid

    # Insert Stock Items
    for item in stock_items:
        cursor.execute("""
            INSERT INTO stock_items (product_id, item_data)
            VALUES (?, ?)
        """, (product_id, item))

    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(
        f"✅ **প্রোডাক্ট সফলভাবে আপলোড হয়েছে!**\n\n"
        f"📦 **নাম:** {title}\n"
        f"💵 **দাম:** {price} BDT\n"
        f"📊 **মোট স্টক:** {len(stock_items)} টি",
        parse_mode="Markdown"
    )
    
