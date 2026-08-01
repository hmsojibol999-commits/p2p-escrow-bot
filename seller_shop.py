import sqlite3
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

seller_router = Router()

def get_connection():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

class ShopState(StatesGroup):
    waiting_for_shop_name = State()
    waiting_for_shop_desc = State()

class ProductState(StatesGroup):
    selecting_category = State()
    waiting_for_title = State()
    waiting_for_price = State()
    waiting_for_stock_data = State()

# 🏪 SELLER SHOP MAIN MENU
@seller_router.message(F.text == "🏪 Seller Dashboard")
@seller_router.message(F.text == "/seller")
async def seller_dashboard(message: types.Message):
    user_id = message.from_user.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shops WHERE seller_id = ?", (user_id,))
    shop = cursor.fetchone()
    conn.close()

    if not shop:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Register Shop", callback_data="register_shop")]
        ])
        await message.answer("🏪 **Apnar kono Seller Shop nei!**\n\nProduct o ID sell korte prothome ekta Shop register korun.", reply_markup=kb, parse_mode="Markdown")
        return

    if shop["status"] == "pending":
        await message.answer("⏳ **Apnar Shop Registration Review-te ache!**\n\nAdmin approve korle apni product add korte parben.", parse_mode="Markdown")
        return

    if shop["status"] == "suspended":
        await message.answer("🔴 **Apnar Shop Suspended kora hoyeche!**\n\nAnugraha kore Support-e jogajog korun.", parse_mode="Markdown")
        return

    text = (
        f"🏪 **{shop['shop_name']}**\n"
        f"⭐ Rating: {shop['rating']} | 📦 Total Sales: {shop['total_sales']}\n\n"
        f"Nicher option babohar kore inventory manage korun:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add New Product/Stock", callback_data="add_product")],
        [InlineKeyboardButton(text="📦 My Listed Products", callback_data="my_products")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# 📝 REGISTER SHOP FLOW
@seller_router.callback_query(F.data == "register_shop")
async def register_shop_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ShopState.waiting_for_shop_name)
    await callback.message.edit_text("📝 Apnar **Shop Name** (Dokaner Nam) likhun:")
    await callback.answer()

@seller_router.message(ShopState.waiting_for_shop_name)
async def process_shop_name(message: types.Message, state: FSMContext):
    shop_name = message.text.strip()
    if len(shop_name) < 3:
        await message.answer("⚠️ Shop Name kompokhe 3 letter-er hote hobe.")
        return
    await state.update_data(shop_name=shop_name)
    await state.set_state(ShopState.waiting_for_shop_desc)
    await message.answer("📝 Shop-er ekta choto **Description** likhun (e.g. Instant Gmail & FB 2FA Provider):")

@seller_router.message(ShopState.waiting_for_shop_desc)
async def process_shop_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    shop_name = data.get("shop_name")
    desc = message.text.strip()
    user_id = message.from_user.id

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO shops (seller_id, shop_name, description, status) VALUES (?, ?, ?, 'approved')",
                       (user_id, shop_name, desc)) # Auto-approved for fast setup/testing
        conn.commit()
        await message.answer(f"🎉 **Congratulations!**\n\nApnar Shop **'{shop_name}'** successfully registered & approved! ekhon `/seller` e giye product add korte parben.", parse_mode="Markdown")
    except sqlite3.IntegrityError:
        await message.answer("⚠️ Apnar ekta Shop agge thekei ache!")
    finally:
        conn.close()

    await state.clear()

# ➕ ADD PRODUCT FLOW
@seller_router.callback_query(F.data == "add_product")
async def add_product_start(callback: types.CallbackQuery, state: FSMContext):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1")
    cats = cursor.fetchall()
    conn.close()

    if not cats:
        await callback.message.edit_text("⚠️ **Marketplace-e ekhono kono Category toiri kora hoyni!**\nAdmin-ke prothome category add korte bolun.")
        await callback.answer()
        return

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📁 {c['name']}", callback_data=f"selcat_{c['id']}")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(ProductState.selecting_category)
    await callback.message.edit_text("📂 **Select Category for your Product:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@seller_router.callback_query(F.data.startswith("selcat_"))
async def category_selected(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=cat_id)
    await state.set_state(ProductState.waiting_for_title)
    await callback.message.edit_text("📝 Product-er ekta **Title / Name** likhun:\n*(e.g. Gmail Fresh 2026 / FB 2FA Cookies ID)*")
    await callback.answer()

@seller_router.message(ProductState.waiting_for_title)
async def process_prod_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(ProductState.waiting_for_price)
    await message.answer("💰 Per Piece Product-er **Price (BDT)** likhun:\n*(e.g. 15.50)*")

@seller_router.message(ProductState.waiting_for_price)
async def process_prod_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Anugraha kore shothik Price (BDT) likhun.")
        return

    await state.update_data(price=price)
    await state.set_state(ProductState.waiting_for_stock_data)
    
    text = (
        "📦 **Upload Digital Items / Accounts Credentials**\n\n"
        "Protiti ID/Account alada line-e likhun:\n"
        "*(Example:)*\n"
        "`user1@gmail.com:pass123:2fa_key1`\n"
        "`user2@gmail.com:pass123:2fa_key2`\n\n"
        "Koyti line thakbe, bot auto counting kore Stock-e add korbe!"
    )
    await message.answer(text, parse_mode="Markdown")

@seller_router.message(ProductState.waiting_for_stock_data)
async def process_prod_stock(message: types.Message, state: FSMContext):
    raw_lines = message.text.strip().split("\n")
    items = [line.strip() for line in raw_lines if line.strip()]

    if not items:
        await message.answer("⚠️ Kono valid credential পাওয়া যায়নি! Abar line by line pathan.")
        return

    data = await state.get_data()
    user_id = message.from_user.id

    conn = get_connection()
    cursor = conn.cursor()
    
    # Get seller shop_id
    cursor.execute("SELECT id FROM shops WHERE seller_id = ?", (user_id,))
    shop = cursor.fetchone()
    shop_id = shop["id"]

    # Insert Product
    cursor.execute(
        "INSERT INTO products (shop_id, category_id, title, price, total_stock) VALUES (?, ?, ?, ?, ?)",
        (shop_id, data["category_id"], data["title"], data["price"], len(items))
    )
    product_id = cursor.lastrowid

    # Insert Items into Stock Locker
    for item in items:
        cursor.execute(
            "INSERT INTO product_stock (product_id, item_data) VALUES (?, ?)",
            (product_id, item)
        )

    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"🎉 **Product Published Successfully!**\n\n📦 **Title:** {data['title']}\n💰 **Price:** {data['price']} BDT\n📊 **Stock Added:** {len(items)} Pcs", parse_mode="Markdown")
  
