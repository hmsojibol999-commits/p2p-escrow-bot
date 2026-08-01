import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from database import init_db, get_connection

# All Routers Import
from admin_panel import admin_router
from wallet import wallet_router
from seller_shop import seller_router
from buyer_marketplace import buyer_router

# ⚙️ CONFIGURATION
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6226350422"))

OFFICIAL_CHANNEL = "@p2p_escrow_official_updates"
PROMO_CHANNEL = "@p2p_escrow_deals_and_promotion"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Include All Routers Engine
dp.include_router(admin_router)
dp.include_router(wallet_router)
dp.include_router(seller_router)
dp.include_router(buyer_router)

# ----------------------------------------------------
# 🔘 KEYBOARD BUILDERS (UI / UX Flow)
# ----------------------------------------------------

# Level 1: Home Reply Keyboard
def main_reply_keyboard(role="buyer"):
    kb = [
        [KeyboardButton(text="🏠 Home"), KeyboardButton(text="🛒 Marketplace")],
        [KeyboardButton(text="💰 Wallet"), KeyboardButton(text="📦 My Orders")],
        [KeyboardButton(text="👤 My Account"), KeyboardButton(text="☎️ Support")]
    ]
    if role == "admin":
        kb.append([KeyboardButton(text="⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Level 2: Marketplace Menu
def marketplace_reply_keyboard(role="buyer"):
    buttons = [
        [KeyboardButton(text="🔍 Browse Products")],
        [KeyboardButton(text="🏪 Become a Seller" if role != "seller" else "🏪 Seller Center")],
        [KeyboardButton(text="📦 My Orders")],
        [KeyboardButton(text="⬅️ Back"), KeyboardButton(text="🏠 Home")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Navigation Buttons Generator (Inline)
def nav_inline_buttons():
    return [
        InlineKeyboardButton(text="⬅️ Back", callback_data="nav_back"),
        InlineKeyboardButton(text="🏠 Home", callback_data="nav_home")
    ]

# ----------------------------------------------------
# 🔍 CHANNEL GUARD & USER VETTING
# ----------------------------------------------------
async def is_user_joined(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=OFFICIAL_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Channel Check Exception: {e}")
        return True

# ----------------------------------------------------
# 🚀 CORE HANDLERS
# ----------------------------------------------------

@dp.message(CommandStart())
@dp.message(F.text == "🏠 Home")
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    user = message.from_user

    # DB Registration
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    
    role = "buyer"
    if not row:
        if user.id == ADMIN_ID:
            role = "admin"
        cursor.execute(
            "INSERT INTO users (user_id, first_name, username, role) VALUES (?, ?, ?, ?)",
            (user.id, user.first_name, user.username or "N/A", role)
        )
        conn.commit()
    else:
        role = row["role"]
    conn.close()

    # Channel Check
    joined = await is_user_joined(user.id)
    if not joined:
        join_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Join Official Channel", url=f"https://t.me/{OFFICIAL_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ I've Joined", callback_data="verify_join")]
        ])
        await message.answer(
            f"👋 **Hello {user.first_name}!**\n\n"
            "⚠️ বটটি ব্যবহার করার আগে আমাদের অফিশিয়াল চ্যানেলে জয়েন করা বাধ্যতামূলক।\n\n"
            "নিচের বাটনে ক্লিক করে জয়েন করুন এবং **`✅ I've Joined`** চাপুন:",
            reply_markup=join_btn,
            parse_mode="Markdown"
        )
        return

    welcome_msg = (
        f"👋 **Welcome to P2P Escrow Marketplace!**\n\n"
        "🔒 **Safe & Automated Digital Goods Trading**\n"
        "✅ Escrow Protection | Verified Sellers | Instant Delivery\n\n"
        "নিচের মেনু থেকে আপনার পছন্দমতো অপশনটি নির্বাচন করুন:"
    )
    await message.answer(welcome_msg, reply_markup=main_reply_keyboard(role), parse_mode="Markdown")

@dp.callback_query(F.data == "verify_join")
async def verify_join_callback(callback: types.CallbackQuery, state: FSMContext):
    joined = await is_user_joined(callback.from_user.id)
    if joined:
        await callback.message.delete()
        await callback.message.answer("✅ **ভেরিফিকেশন সফল হয়েছে!**")
        await send_welcome(callback.message, state)
    else:
        await callback.answer("❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

# 🛒 MARKETPLACE MENU
@dp.message(F.text == "🛒 Marketplace")
@dp.message(F.text == "⬅️ Back")
async def open_marketplace(message: types.Message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (message.from_user.id,))
    row = cursor.fetchone()
    role = row["role"] if row else "buyer"
    conn.close()

    text = (
        "🛒 **Marketplace Center**\n\n"
        "এখানে আপনি বিভিন্ন ডিজিটাল প্রোডাক্ট ব্রাউজ করতে পারবেন বা সেলার হিসেবে যুক্ত হতে পারবেন।\n\n"
        "একটি অপশন বেছে নিন:"
    )
    await message.answer(text, reply_markup=marketplace_reply_keyboard(role), parse_mode="Markdown")

# 🔍 BROWSE PRODUCTS & CATEGORIES
@dp.message(F.text == "🔍 Browse Products")
async def browse_products(message: types.Message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE status = 'active'")
    categories = cursor.fetchall()
    conn.close()

    if not categories:
        text = (
            "📦 **বর্তমানে কোনো ক্যাটাগরি তৈরি করা হয়নি!**\n\n"
            "এডমিন নতুন ক্যাটাগরি যোগ করলে এখানে দেখতে পাবেন।"
        )
        await message.answer(text, parse_mode="Markdown")
        return

    inline_kb = []
    for cat in categories:
        inline_kb.append([InlineKeyboardButton(text=f"📁 {cat['name']}", callback_data=f"cat_{cat['id']}")])
    
    inline_kb.append(nav_inline_buttons())

    await message.answer(
        "📂 **ক্যাটাগরি নির্বাচন করুন:**\n\nযে ধরণের প্রোডাক্ট কিনতে চান তার ক্যাটাগরিতে চাপ দিন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb),
        parse_mode="Markdown"
    )

# 🏪 BECOME A SELLER
@dp.message(F.text == "🏪 Become a Seller")
async def apply_seller(message: types.Message):
    text = (
        "🏪 **Apply to Become a Seller**\n\n"
        "প্লাটফর্মে বিক্রেতা (Seller) হতে এডমিনের অনুমতির প্রয়োজন।\n\n"
        "⚠️ **সেলার নীতিমালা:**\n"
        "১. শুধুমাত্র বৈধ ও সঠিক প্রোডাক্ট বিক্রি করতে হবে।\n"
        "২. কোনো প্রতারণা বা স্প্যাম করার চেষ্টা করলে একাউন্ট স্থায়ীভাবে ব্যালেন্সসহ ব্যান করা হবে।\n\n"
        "আপনি কি সেলার আবেদনের জন্য প্রস্তুত?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Apply to Admin", callback_data="req_seller_apply")],
        nav_inline_buttons()
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# 💰 WALLET
@dp.message(F.text == "💰 Wallet")
async def show_wallet(message: types.Message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (message.from_user.id,))
    row = cursor.fetchone()
    balance = row["balance"] if row else 0.0
    conn.close()

    text = (
        "💰 **Your Account Wallet**\n\n"
        f"💵 **Current Balance:** `{balance:.2f} BDT`\n"
        "🔒 **Escrow Protection:** Active\n\n"
        "নিচের বাটন দিয়ে ডিপোজিট বা উইথড্র ফান্ড ম্যানেজ করুন:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Deposit", callback_data="wallet_deposit"),
            InlineKeyboardButton(text="➖ Withdraw", callback_data="wallet_withdraw")
        ],
        [InlineKeyboardButton(text="📜 Transaction History", callback_data="wallet_history")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# 👤 MY ACCOUNT
@dp.message(F.text == "👤 My Account")
async def my_account(message: types.Message):
    user = message.from_user
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, trust_score, balance FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()

    role = row["role"] if row else "buyer"
    trust = row["trust_score"] if row else 100
    balance = row["balance"] if row else 0.0

    text = (
        f"👤 **Account Overview**\n\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"👤 **Name:** {user.first_name}\n"
        f"🎭 **Role:** `{role.upper()}`\n"
        f"⭐ **Trust Score:** `{trust}/100`\n"
        f"💰 **Balance:** `{balance:.2f} BDT`"
    )
    await message.answer(text, parse_mode="Markdown")

# ☎️ SUPPORT
@dp.message(F.text == "☎️ Support")
async def support_center(message: types.Message):
    text = (
        "☎️ **Support & Help Desk**\n\n"
        "আপনার কোনো প্রশ্ন, সমস্যা বা সহায়তার প্রয়োজন হলে আমাদের সাপোর্টে যোগাযোগ করুন।\n\n"
        "📢 **Official Channel:** @p2p_escrow_official_updates\n"
        "💬 **Admin Contact:** @Sojib_Admin"
    )
    await message.answer(text, parse_mode="Markdown")

# Nav Callbacks
@dp.callback_query(F.data == "nav_home")
async def cb_nav_home(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await send_welcome(callback.message, state)

# ----------------------------------------------------
# ⚙️ SERVER & POLLING
# ----------------------------------------------------
async def handle_health(request):
    return web.Response(text="P2P Escrow Engine Online")

async def main():
    init_db()
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("🚀 Bot Engine Running Successfully...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
