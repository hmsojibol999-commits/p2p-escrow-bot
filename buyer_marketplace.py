import sqlite3
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

buyer_router = Router()

def get_connection():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

class BuyState(StatesGroup):
    waiting_for_quantity = State()

# 🛍️ MARKETPLACE MAIN MENU / BROWSE CATEGORIES
@buyer_router.message(F.text == "🛍️ Buy Products")
@buyer_router.message(F.text == "/shop")
async def browse_marketplace(message: types.Message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1")
    cats = cursor.fetchall()
    conn.close()

    if not cats:
        await message.answer("🛍️ **Marketplace-e ekhono kono category live nei!**\nKhub shighroi notun inventory add kora hobe.")
        return

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📁 {c['name']}", callback_data=f"buycat_{c['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("🛍️ **MARKETPLACE CATEGORIES**\n\nProduct o ID kinte niche theke category select korun:", reply_markup=kb, parse_mode="Markdown")

# 📂 SHOW PRODUCTS IN SELECTED CATEGORY
@buyer_router.callback_query(F.data.startswith("buycat_"))
async def show_category_products(callback: types.CallbackQuery):
    cat_id = int(callback.data.split("_")[1])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.*, s.shop_name, s.rating 
        FROM products p
        JOIN shops s ON p.shop_id = s.id
        WHERE p.category_id = ? AND p.status = 'active' AND p.total_stock > 0
    """, (cat_id,))
    
    prods = cursor.fetchall()
    conn.close()

    if not prods:
        await callback.message.edit_text("⚠️ **Ei category-te ekhono kono stock available nei!**\nOnno category try korun.")
        await callback.answer()
        return

    text = "📦 **AVAILABLE PRODUCTS & STOCKS:**\n\n"
    buttons = []
    for p in prods:
        text += (
            f"🔹 **{p['title']}**\n"
            f"🏪 Shop: {p['shop_name']} (⭐ {p['rating']})\n"
            f"💰 Price: **{p['price']:.2f} BDT** / pc\n"
            f"📊 Stock Available: **{p['total_stock']} Pcs**\n"
            "-----------------------------------\n"
        )
        buttons.append([InlineKeyboardButton(text=f"🛒 Buy: {p['title']} ({p['price']} BDT)", callback_data=f"buyprod_{p['id']}")])

    buttons.append([InlineKeyboardButton(text="🔙 Back to Categories", callback_data="back_buycats")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@buyer_router.callback_query(F.data == "back_buycats")
async def back_to_buy_cats(callback: types.CallbackQuery):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1")
    cats = cursor.fetchall()
    conn.close()

    buttons = []
    for c in cats:
        buttons.append([InlineKeyboardButton(text=f"📁 {c['name']}", callback_data=f"buycat_{c['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("🛍️ **MARKETPLACE CATEGORIES**\n\nProduct o ID kinte niche theke category select korun:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# 🛒 START BUY PROCESS (ESCROW LOCK)
@buyer_router.callback_query(F.data.startswith("buyprod_"))
async def init_purchase(callback: types.CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split("_")[1])
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
    product = cursor.fetchone()
    conn.close()

    if not product or product["total_stock"] <= 0:
        await callback.message.edit_text("⚠️ **Dukhito! Ei product-ti stock out hoye geche.**")
        await callback.answer()
        return

    await state.update_data(buy_product_id=prod_id, unit_price=product["price"], max_stock=product["total_stock"])
    await state.set_state(BuyState.waiting_for_quantity)

    text = (
        f"🛒 **Buy Product:** {product['title']}\n"
        f"💰 Price per pc: **{product['price']:.2f} BDT**\n"
        f"📊 Max Available: **{product['total_stock']} Pcs**\n\n"
        f"Apni koy piece kinte chan shongkhya likhun (e.g. 1, 5, 10):"
    )
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

# 📦 PROCESS QUANTITY, BALANCE DEDUCTION & ESCROW AUTO-DELIVERY
@buyer_router.message(BuyState.waiting_for_quantity)
async def process_purchase_quantity(message: types.Message, state: FSMContext):
    try:
        qty = int(message.text.strip())
        if qty <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Anugraha kore shothik shongkhya likhun (e.g. 1, 5, 10).")
        return

    data = await state.get_data()
    prod_id = data.get("buy_product_id")
    unit_price = data.get("unit_price")
    max_stock = data.get("max_stock")

    if qty > max_stock:
        await message.answer(f"⚠️ Stock-e matro **{max_stock} Pcs** ache. Anugraha kore kom shongkhya likhun.")
        return

    total_cost = qty * unit_price
    buyer_id = message.from_user.id

    conn = get_connection()
    cursor = conn.cursor()

    # Check Buyer Wallet Balance
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (buyer_id,))
    user_row = cursor.fetchone()
    buyer_balance = user_row["balance"] if user_row else 0.0

    if buyer_balance < total_cost:
        await message.answer(
            f"⚠️ **Insufficient Balance!**\n\n"
            f"Apnar kache **{buyer_balance:.2f} BDT** ache, kintu dorkar **{total_cost:.2f} BDT**.\n"
            f"💳 Prothome `/deposit` kore balance add korun.",
            parse_mode="Markdown"
        )
        await state.clear()
        conn.close()
        return

    # Fetch Credentials from Stock Locker
    cursor.execute(
        "SELECT id, item_data FROM product_stock WHERE product_id = ? AND is_sold = 0 LIMIT ?",
        (prod_id, qty)
    )
    stock_items = cursor.fetchall()

    if len(stock_items) < qty:
        await message.answer("⚠️ Dukhito! Ei muhurte jothesto stock available nei.")
        await state.clear()
        conn.close()
        return

    stock_ids = [item["id"] for item in stock_items]
    delivered_data = "\n".join([item["item_data"] for item in stock_items])

    # 1. Deduct Buyer Balance
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (total_cost, buyer_id))

    # 2. Mark Stock as Sold
    cursor.execute(
        f"UPDATE product_stock SET is_sold = 1, sold_to_user_id = ?, sold_at = CURRENT_TIMESTAMP WHERE id IN ({','.join(['?']*len(stock_ids))})",
        [buyer_id] + stock_ids
    )

    # 3. Update Product Stock Count
    cursor.execute("UPDATE products SET total_stock = total_stock - ? WHERE id = ?", (qty, prod_id))

    # 4. Get Seller Info & Create Escrow Trade Record
    cursor.execute("SELECT s.seller_id FROM products p JOIN shops s ON p.shop_id = s.id WHERE p.id = ?", (prod_id,))
    seller_row = cursor.fetchone()
    seller_id = seller_row["seller_id"] if seller_row else None

    commission = total_cost * 0.01  # 1% Platform Commission Policy

    cursor.execute(
        "INSERT INTO escrow_trades (buyer_id, seller_id, product_id, quantity, total_price, commission_amount, status) VALUES (?, ?, ?, ?, ?, ?, 'holding')",
        (buyer_id, seller_id, prod_id, qty, total_cost, commission)
    )
    escrow_id = cursor.lastrowid

    conn.commit()
    conn.close()

    await state.clear()

    # 📩 INSTANT DIGITAL DELIVERY MESSAGE TO BUYER
    success_text = (
        f"🎉 **PURCHASE SUCCESSFUL (#ESCROW{escrow_id})**\n\n"
        f"💰 **Total Deducted:** {total_cost:.2f} BDT\n"
        f"📦 **Quantity Delivered:** {qty} Pcs\n"
        f"🛡️ **Escrow Status:** Held in Secure Locker (30 Mins Timer Active)\n\n"
        f"🔑 **YOUR CREDENTIALS / PRODUCTS:**\n"
        f"```text\n{delivered_data}\n```\n\n"
        f"⚠️ *Anugraha kore credentials gulo safe jaygay save korun.*"
    )
    await message.answer(success_text, parse_mode="Markdown")
  
