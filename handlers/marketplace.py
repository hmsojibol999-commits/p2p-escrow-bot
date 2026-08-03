from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db

router = Router()

@router.callback_query(F.data == "menu_marketplace")
async def marketplace_categories(callback: CallbackQuery):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()

    if not categories:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]])
        await callback.message.edit_text("🛒 বর্তমানে কোনো ক্যাটাগরি উপলব্ধ নেই।", reply_markup=keyboard)
        await callback.answer()
        return

    buttons = [[InlineKeyboardButton(text=cat["name"], callback_data=f"market_cat_{cat['id']}")] for cat in categories]
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])
    
    await callback.message.edit_text("🛒 **Marketplace Categories**\n\nএকটি ক্যাটাগরি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("market_cat_"))
async def marketplace_products(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[2])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, price FROM products WHERE category_id = ?", (cat_id,))
        products = cursor.fetchall()

    if not products:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="menu_marketplace")]])
        await callback.message.edit_text("📦 এই ক্যাটাগরিতে কোনো প্রোডাক্ট নেই।", reply_markup=keyboard)
        await callback.answer()
        return

    buttons = []
    for p in products:
        # Check stock count
        cursor.execute("SELECT COUNT(*) as cnt FROM product_items WHERE product_id = ? AND is_sold = 0", (p["id"],))
        stock = cursor.fetchone()["cnt"]
        buttons.append([InlineKeyboardButton(text=f"{p['title']} - ৳{p['price']} (Stock: {stock})", callback_data=f"market_prod_{p['id']}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu_marketplace")])

    await callback.message.edit_text("📦 **Products List**\n\nপ্রোডাক্ট সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("market_prod_"))
async def product_details(callback: CallbackQuery):
    prod_id = int(callback.data.split("_")[2])
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
        product = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as cnt FROM product_items WHERE product_id = ? AND is_sold = 0", (prod_id,))
        stock = cursor.fetchone()["cnt"]

    if not product:
        await callback.answer("⚠️ প্রোডাক্ট পাওয়া যায়নি।", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Buy Now", callback_data=f"buy_prod_{prod_id}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"market_cat_{product['category_id']}")]
    ])

    await callback.message.edit_text(
        f"🛍 **{product['title']}**\n\n"
        f"💰 Price: ৳{product['price']}\n"
        f"📦 Available Stock: {stock}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_prod_"))
async def buy_product(callback: CallbackQuery):
    user_id = callback.from_user.id
    prod_id = int(callback.data.split("_")[2])

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
        product = cursor.fetchone()
        
        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        wallet = cursor.fetchone()
        balance = wallet["balance"] if wallet else 0.0

        if balance < product["price"]:
            await callback.answer("⚠️ আপনার পর্যাপ্ত ব্যালেন্স নেই! দয়া করে ডিপোজিট করুন।", show_alert=True)
            return

        # Fetch available stock item
        cursor.execute("SELECT id, content FROM product_items WHERE product_id = ? AND is_sold = 0 LIMIT 1", (prod_id,))
        item = cursor.fetchone()

        if not item:
            await callback.answer("⚠️ বর্তমানে স্টক শেষ হয়ে গেছে!", show_alert=True)
            return

        item_id = item["id"]
        item_content = item["content"]

        # Deduct balance, mark item sold, insert order & transaction
        cursor.execute("UPDATE wallets SET balance = balance - ? WHERE user_id = ?", (product["price"], user_id))
        cursor.execute("UPDATE product_items SET is_sold = 1 WHERE id = ?", (item_id,))
        cursor.execute("""
            INSERT INTO orders (user_id, product_id, item_content, price, status)
            VALUES (?, ?, ?, ?, 'completed')
        """, (user_id, prod_id, item_content, product["price"]))
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (?, 'purchase', ?, ?)
        """, (user_id, product["price"], f"Bought {product['title']}"))
        conn.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Marketplace", callback_data="menu_marketplace")]])
    await callback.message.edit_text(
        f"✅ **Purchase Successful!**\n\n"
        f"🛍 Product: {product['title']}\n"
        f"🔑 **Details:**\n`{item_content}`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "menu_orders")
async def my_orders(callback: CallbackQuery):
    user_id = callback.from_user.id
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.item_content, o.price, o.created_at, p.title 
            FROM orders o JOIN products p ON o.product_id = p.id 
            WHERE o.user_id = ? ORDER BY o.id DESC LIMIT 10
        """, (user_id,))
        orders = cursor.fetchall()

    if not orders:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]])
        await callback.message.edit_text("📦 আপনার কোনো অর্ডার হিস্ট্রি নেই।", reply_markup=keyboard)
        await callback.answer()
        return

    text = "📦 **Your Recent Orders:**\n\n"
    for o in orders:
        text += f"• **{o['title']}** - ৳{o['price']}\n  Details: `{o['item_content']}`\n  Date: {o['created_at']}\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
  
