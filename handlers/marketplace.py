import logging
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database import Database

logger = logging.getLogger(__name__)
router = Router()
db = Database()

def get_utc_now() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# ================= Keyboards =================
def get_marketplace_menu_keyboard() -> InlineKeyboardMarkup:
    """Generates back button to main menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="menu_main")]
    ])

# ================= Marketplace Entry & Categories =================
@router.callback_query(F.data == "menu_marketplace")
async def show_categories(callback: CallbackQuery) -> None:
    """Displays all available categories from the database."""
    try:
        await db.connect()
        categories = await db.fetchall("SELECT id, name, description FROM categories ORDER BY id ASC;")

        if not categories:
            text = "🛒 <b>ডিজিটাল মার্কেটপ্লেস</b>\n\nদুঃখিত, বর্তমানে কোনো ক্যাটাগরি উপলব্ধ নেই।"
            try:
                await callback.message.edit_text(text, reply_markup=get_marketplace_menu_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(text, reply_markup=get_marketplace_menu_keyboard())
            await callback.answer()
            return

        keyboard_buttons = []
        for cat in categories:
            cat_name = cat["name"]
            cat_id = cat["id"]
            keyboard_buttons.append([InlineKeyboardButton(text=f"📂 {cat_name}", callback_data=f"market_cat_{cat_id}")])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="menu_main")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        text = "🛒 <b>ডিজিটাল মার্কেটপ্লেস</b>\n\nঅনুগ্রহ করে আপনার পছন্দের ক্যাটাগরি সিলেক্ট করুন:"
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing categories: {e}")
        await callback.answer("⚠️ মার্কেটপ্লেস লোড করতে সমস্যা হয়েছে।", show_alert=True)

# ================= Product List by Category =================
@router.callback_query(F.data.startswith("market_cat_"))
async def show_products_by_category(callback: CallbackQuery) -> None:
    """Displays products for the selected category with live stock calculated from product_items."""
    cat_id_str = callback.data.replace("market_cat_", "", 1)
    try:
        cat_id = int(cat_id_str)
    except ValueError:
        await callback.answer("⚠️ অবৈধ ক্যাটাগরি আইডি।", show_alert=True)
        return

    try:
        await db.connect()
        category = await db.fetchone("SELECT name FROM categories WHERE id = ?;", (cat_id,))
        if not category:
            await callback.answer("⚠️ ক্যাটাগরি পাওয়া যায়নি।", show_alert=True)
            return

        cat_name = category["name"]

        # Fetch products and calculate stock count dynamically from product_items where sold = 0
        products = await db.fetchall(
            """
            SELECT p.id, p.title, p.price, 
                   (SELECT COUNT(*) FROM product_items pi WHERE pi.product_id = p.id AND pi.sold = 0) as stock_count
            FROM products p
            WHERE p.category_id = ? AND p.status = 'active'
            ORDER BY p.id DESC;
            """,
            (cat_id,)
        )

        keyboard_buttons = []
        if products:
            for p in products:
                p_title = p["title"]
                p_id = p["id"]
                p_price = p["price"]
                stock = p["stock_count"]
                
                stock_text = f"📦 Stock: {stock}" if stock > 0 else "❌ Out of Stock"
                btn_text = f"{p_title} — ৳{p_price:.2f} ({stock_text})"
                keyboard_buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"market_prod_{p_id}")])

        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Back to Categories", callback_data="menu_marketplace")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        text = f"📂 ক্যাটাগরি: <b>{cat_name}</b>\n\nপণ্য তালিকা নিচে দেওয়া হলো:"
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error loading products for category {cat_id}: {e}")
        await callback.answer("⚠️ পণ্য তালিকা লোড করতে সমস্যা হয়েছে।", show_alert=True)

# ================= Product Details & Buy Option =================
@router.callback_query(F.data.startswith("market_prod_"))
async def show_product_details(callback: CallbackQuery) -> None:
    """Displays detailed product info, description, price, and live stock count."""
    prod_id_str = callback.data.replace("market_prod_", "", 1)
    try:
        prod_id = int(prod_id_str)
    except ValueError:
        await callback.answer("⚠️ অবৈধ পণ্য আইডি।", show_alert=True)
        return

    try:
        await db.connect()
        product = await db.fetchone(
            """
            SELECT p.id, p.category_id, p.title, p.description, p.price, p.status,
                   (SELECT COUNT(*) FROM product_items pi WHERE pi.product_id = p.id AND pi.sold = 0) as stock_count
            FROM products p
            WHERE p.id = ?;
            """,
            (prod_id,)
        )

        if not product or product["status"] != "active":
            await callback.answer("⚠️ পণ্যটি বর্তমানে উপলব্ধ নেই।", show_alert=True)
            return

        title = product["title"]
        description = product["description"] or "বিবরণ নেই"
        price = product["price"]
        stock = product["stock_count"]
        cat_id = product["category_id"]

        text = (
            f"📦 <b>{title}</b>\n\n"
            f"📝 বিবরণ: {description}\n\n"
            f"💰 মূল্য: <b>৳{price:.2f}</b>\n"
            f"📊 বর্তমান স্টক: <b>{stock} টি</b>"
        )

        keyboard_buttons = []
        if stock > 0:
            keyboard_buttons.append([InlineKeyboardButton(text="🛒 Buy Now", callback_data=f"market_buy_{prod_id}")])
        else:
            keyboard_buttons.append([InlineKeyboardButton(text="❌ Out of Stock", callback_data="market_nostock")])

        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Back to Products", callback_data=f"market_cat_{cat_id}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing product details {prod_id}: {e}")
        await callback.answer("⚠️ পণ্যের তথ্য লোড করতে সমস্যা হয়েছে।", show_alert=True)

@router.callback_query(F.data == "market_nostock")
async def notify_out_of_stock(callback: CallbackQuery) -> None:
    """Alerts user that the product is currently out of stock."""
    await callback.answer("⚠️ দুঃখিত, এই পণ্যটি বর্তমানে স্টক আউট রয়েছে!", show_alert=True)

# ================= Buy Flow & Atomic Digital Delivery =================
@router.callback_query(F.data.startswith("market_buy_"))
async def process_product_purchase(callback: CallbackQuery) -> None:
    """Handles secure atomic purchase, inventory delivery, wallet deduction, order & transaction logging."""
    prod_id_str = callback.data.replace("market_buy_", "", 1)
    try:
        prod_id = int(prod_id_str)
    except ValueError:
        await callback.answer("⚠️ অবৈধ পণ্য আইডি।", show_alert=True)
        return

    user_id = callback.from_user.id
    now = get_utc_now()

    try:
        await db.connect()

        # 1. Fetch user wallet balance
        wallet = await db.fetchone("SELECT balance FROM wallets WHERE telegram_id = ?;", (user_id,))
        balance = wallet["balance"] if wallet else 0.0

        # 2. Fetch product details
        product = await db.fetchone("SELECT title, price, category_id FROM products WHERE id = ? AND status = 'active';", (prod_id,))
        if not product:
            await callback.answer("⚠️ পণ্যটি পাওয়া যায়নি বা নিষ্ক্রিয় করা হয়েছে।", show_alert=True)
            return

        price = product["price"]
        title = product["title"]
        cat_id = product["category_id"]

        # 3. Check wallet balance sufficiency
        if balance < price:
            await callback.answer(
                f"⚠️ পর্যাপ্ত ব্যালেন্স নেই! আপনার ব্যালেন্স: ৳{balance:.2f} (প্রয়োজনীয়: ৳{price:.2f}). দয়া করে ডিপোজিট করুন।",
                show_alert=True
            )
            return

        # 4. Begin Atomic Transaction & Concurrency Safety
        await db.begin()
        try:
            # Re-check stock atomically inside transaction block
            item = await db.fetchone(
                "SELECT id, content FROM product_items WHERE product_id = ? AND sold = 0 LIMIT 1;",
                (prod_id,)
            )

            if not item:
                await db.rollback()
                await callback.answer("⚠️ দুঃখিত, এই মুহূর্তে পণ্যটি স্টক আউট হয়ে গেছে!", show_alert=True)
                return

            item_id = item["id"]
            item_content = item["content"]

            # 5. Insert Order Record first to get order_id
            order_cursor = await db.execute(
                """
                INSERT INTO orders (telegram_id, product_id, item_content, price, status, created_at)
                VALUES (?, ?, ?, ?, 'completed', ?);
                """,
                (user_id, prod_id, item_content, price, now)
            )
            order_id = order_cursor.lastrowid

            # 6. Mark specific inventory item as sold, update sold_at and order_id
            await db.execute(
                """
                UPDATE product_items 
                SET sold = 1, sold_at = ?, order_id = ? 
                WHERE id = ? AND sold = 0;
                """,
                (now, order_id, item_id)
            )

            # 7. Deduct wallet balance and increment total_spent
            await db.execute(
                """
                UPDATE wallets 
                SET balance = balance - ?, total_spent = total_spent + ? 
                WHERE telegram_id = ?;
                """,
                (price, price, user_id)
            )

            # 8. Record transaction history of type 'purchase'
            await db.execute(
                """
                INSERT INTO transactions (telegram_id, type, amount, description, created_at)
                VALUES (?, 'purchase', ?, ?, ?);
                """,
                (user_id, price, f"Purchased: {title} (#ORD{order_id})", now)
            )

            # 9. Update user total orders count
            await db.execute(
                "UPDATE users SET total_orders = total_orders + 1, last_activity = ? WHERE telegram_id = ?;",
                (now, user_id)
            )

            await db.commit()
        except Exception as tx_err:
            await db.rollback()
            logger.error(f"Atomic purchase transaction failed for user {user_id}, product {prod_id}: {tx_err}")
            await callback.answer("⚠️ ক্রয়ের সময় প্রযুক্তিগত ত্রুটি ঘটেছে। আবার চেষ্টা করুন।", show_alert=True)
            return

        # 10. Deliver Digital Product Content to User
        success_text = (
            f"🎉 <b>ক্রয় সফল হয়েছে! (#ORD{order_id})</b>\n\n"
            f"📦 পণ্য: <b>{title}</b>\n"
            f"💰 মূল্য: ৳{price:.2f}\n\n"
            f"🔑 <b>আপনার ডিজিটাল পণ্য/ইনভেন্টরি:</b>\n"
            f"<code>{item_content}</code>\n\n"
            f"দয়া করে তথ্যগুলো সংরক্ষণ করে রাখুন।"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 My Orders", callback_data="menu_orders")],
            [InlineKeyboardButton(text="🛒 Back to Marketplace", callback_data="menu_marketplace")]
        ])

        try:
            await callback.message.edit_text(success_text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(success_text, reply_markup=keyboard)

        await callback.answer("✅ সফলভাবে ক্রয় সম্পন্ন হয়েছে!")

    except Exception as e:
        logger.error(f"Error processing purchase for user {user_id}: {e}")
        await callback.answer("⚠️ একটি ত্রুটি ঘটেছে। পরে আবার চেষ্টা করুন।", show_alert=True)

# ================= My Orders Handler =================
@router.callback_query(F.data == "menu_orders")
async def show_user_orders(callback: CallbackQuery) -> None:
    """Displays recent order history for the user with future-ready pagination structure."""
    user_id = callback.from_user.id
    try:
        await db.connect()
        orders = await db.fetchall(
            """
            SELECT o.id, o.item_content, o.price, o.created_at, p.title 
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.telegram_id = ?
            ORDER BY o.id DESC LIMIT 10;
            """,
            (user_id,)
        )

        text = "📦 <b>আপনার অর্ডার হিস্ট্রি</b>\n\n"
        if not orders:
            text += "আপনার কোনো অর্ডার রেকর্ড নেই।"
        else:
            for o in orders:
                o_id = o["id"]
                p_title = o["title"]
                price = o["price"]
                content = o["item_content"]
                date = o["created_at"][:19].replace("T", " ")
                text += f"• <b>#{o_id} - {p_title}</b> (৳{price:.2f})\n  🔑 <code>{content}</code>\n  🕒 {date}\n\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Marketplace", callback_data="menu_marketplace")],
            [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="menu_main")]
        ])

        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error fetching orders for user {user_id}: {e}")
        await callback.answer("⚠️ অর্ডার হিস্ট্রি লোড করতে সমস্যা হয়েছে।", show_alert=True)
            
