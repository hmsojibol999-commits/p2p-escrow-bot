from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_connection

buyer_router = Router()

# 🔍 BROWSE CATEGORY PRODUCTS
@buyer_router.callback_query(F.data.startswith("cat_"))
async def show_category_products(callback: types.CallbackQuery):
    cat_id = int(callback.data.split("_")[1])
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.title, p.price, COUNT(s.id) as stock_count 
        FROM products p
        LEFT JOIN stock_items s ON p.id = s.product_id AND s.status = 'available'
        WHERE p.category_id = ? AND p.status = 'approved'
        GROUP BY p.id
    """, (cat_id,))
    products = cursor.fetchall()
    conn.close()

    if not products:
        await callback.answer("⚠️ এই ক্যাটাগরিতে বর্তমানে কোনো প্রোডাক্ট নেই!", show_alert=True)
        return

    text = "🛒 **উপলব্ধ প্রোডাক্টসমূহ:**\n\nযে প্রোডাক্টটি কিনতে চান তার ওপর চাপ দিন:\n"
    kb = []
    for p in products:
        stock_text = f"({p['stock_count']} টি স্টকে আছে)" if p['stock_count'] > 0 else "(Out of Stock)"
        kb.append([InlineKeyboardButton(
            text=f"📦 {p['title']} - {p['price']} BDT {stock_text}", 
            callback_data=f"buy_prod_{p['id']}"
        )])
    
    kb.append([InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

# 💳 BUY PRODUCT & AUTOMATED DELIVERY (ESCROW HOLD)
@buyer_router.callback_query(F.data.startswith("buy_prod_"))
async def process_buy_product(callback: types.CallbackQuery):
    prod_id = int(callback.data.split("_")[2])
    buyer_id = callback.from_user.id

    conn = get_connection()
    cursor = conn.cursor()

    # Get Product & Stock Info
    cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        await callback.answer("❌ প্রোডাক্টটি পাওয়া যায়নি!", show_alert=True)
        return

    # Check Buyer Balance
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (buyer_id,))
    user_row = cursor.fetchone()
    balance = user_row["balance"] if user_row else 0.0

    if balance < product["price"]:
        conn.close()
        await callback.answer(
            f"❌ পর্যাপ্ত ব্যালেন্স নেই!\nপ্রয়োজন: {product['price']} BDT\nআপনার আছে: {balance} BDT\n\nঅনুগ্রহ করে ওয়ালেটে ডিপোজিট করুন।",
            show_alert=True
        )
        return

    # Check Available Stock Item
    cursor.execute("SELECT * FROM stock_items WHERE product_id = ? AND status = 'available' LIMIT 1", (prod_id,))
    stock_item = cursor.fetchone()

    if not stock_item:
        conn.close()
        await callback.answer("❌ দুঃখিত! এই প্রোডাক্টটির স্টক শেষ হয়ে গেছে।", show_alert=True)
        return

    # 🔄 ESCROW TRANSACTION EXECUTION
    # 1. Deduct Balance
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (product["price"], buyer_id))
    
    # 2. Mark Stock as Sold
    cursor.execute("UPDATE stock_items SET status = 'sold' WHERE id = ?", (stock_item["id"],))

    # 3. Create Escrow Order
    cursor.execute("""
        INSERT INTO orders (buyer_id, seller_id, product_id, quantity, total_price, escrow_status, delivered_data)
        VALUES (?, ?, ?, 1, ?, 'held', ?)
    """, (buyer_id, product["seller_id"], prod_id, product["price"], stock_item["item_data"]))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Instant Delivery Message
    delivery_text = (
        f"🎉 **অর্ডার সফল হয়েছে! (Order #{order_id})**\n\n"
        f"📦 **প্রোডাক্ট:** {product['title']}\n"
        f"💵 **মূল্য:** {product['price']} BDT\n"
        f"🔒 **Escrow Status:** `Funds Held Safely`\n\n"
        f"🔑 **আপনার ডেলিভারি ডেটা (Stock Credentials):**\n"
        f"```\n{stock_item['item_data']}\n```\n\n"
        "⚠️ **নির্দেশনা:** অ্যাকাউন্ট চেক করে নিশ্চিত হন। সমস্যা থাকলে Support-এ যোগাযোগ করুন।"
    )
    
    await callback.message.answer(delivery_text, parse_mode="Markdown")
    
