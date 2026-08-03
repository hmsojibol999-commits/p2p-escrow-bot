from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from database import db
from config import REQUIRED_CHANNEL_1, REQUIRED_CHANNEL_2

router = Router()

async def check_channels(bot, user_id: int) -> bool:
    channels = [REQUIRED_CHANNEL_1, REQUIRED_CHANNEL_2]
    for ch in channels:
        if ch:
            try:
                member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    return False
            except Exception:
                return False
    return True

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Marketplace", callback_data="menu_marketplace"),
         InlineKeyboardButton(text="💼 Wallet", callback_data="menu_wallet")],
        [InlineKeyboardButton(text="📦 My Orders", callback_data="menu_orders"),
         InlineKeyboardButton(text="👤 Profile", callback_data="menu_profile")],
        [InlineKeyboardButton(text="💬 Support", callback_data="menu_support")]
    ])

def get_channel_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    if REQUIRED_CHANNEL_1:
        buttons.append([InlineKeyboardButton(text="Join Channel 1", url=f"https://t.me/{REQUIRED_CHANNEL_1.replace('@', '')}")])
    if REQUIRED_CHANNEL_2:
        buttons.append([InlineKeyboardButton(text="Join Channel 2", url=f"https://t.me/{REQUIRED_CHANNEL_2.replace('@', '')}")])
    buttons.append([InlineKeyboardButton(text="🔄 Check / Refresh", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    # Save user to DB if not exists
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        cursor.execute("INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (?, 0.0)", (user_id,))
        conn.commit()

    is_joined = await check_channels(message.bot, user_id)
    if not is_joined:
        await message.answer(
            "⚠️ অনুগ্রহ করে আমাদের অফিশিয়াল চ্যানেলগুলোতে জয়েন করুন এবং তারপর নিচে 'Check / Refresh' বাটনে ক্লিক করুন।",
            reply_markup=get_channel_keyboard()
        )
        return

    await message.answer(
        "👋 স্বাগতম! আপনার প্রয়োজনীয় সেবা নিচের মেনু থেকে বেছে নিন:",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_joined = await check_channels(callback.bot, user_id)
    
    if not is_joined:
        await callback.answer("⚠️ আপনি এখনো সব চ্যানেলে জয়েন করেননি!", show_alert=True)
        return

    await callback.message.edit_text(
        "👋 স্বাগতম! আপনার প্রয়োজনীয় সেবা নিচের মেনু থেকে বেছে নিন:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
  
