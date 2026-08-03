from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import SUPPORT_ADMIN_ID

router = Router()

@router.callback_query(F.data == "menu_profile")
async def profile_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "NoUsername"

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT join_date FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        join_date = user["join_date"] if user else "N/A"

        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        wallet = cursor.fetchone()
        balance = wallet["balance"] if wallet else 0.0

        cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id = ?", (user_id,))
        order_count = cursor.fetchone()["cnt"]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Become a Seller", callback_data="become_seller")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])

    await callback.message.edit_text(
        f"👤 **User Profile**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"🔗 Username: @{username}\n"
        f"📅 Join Date: {join_date}\n"
        f"💰 Wallet Balance: ৳{balance:.2f}\n"
        f"📦 Total Orders: {order_count}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "become_seller")
async def become_seller(callback: CallbackQuery):
    sup_btn = InlineKeyboardButton(text="💬 Contact Support Admin", callback_data="menu_support")
    back_btn = InlineKeyboardButton(text="🔙 Back", callback_data="menu_profile")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[sup_btn], [back_btn]])

    await callback.message.edit_text(
        "💼 **Become a Seller**\n\nSeller হতে চাইলে Support Admin-এর সাথে যোগাযোগ করুন।",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
  
