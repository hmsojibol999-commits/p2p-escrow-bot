import logging
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from config import REQUIRED_CHANNEL_1, REQUIRED_CHANNEL_2, SUPPORT_ADMIN_ID
from database import Database

logger = logging.getLogger(__name__)
router = Router()

# Global database instance reference (initialized via main.py / imported safely if needed, 
# but since database.py provides class, we instantiate or import the DB connection wrapper 
# matching the architecture. Wait, main.py instantiates `db = Database()`. Let's import `db` 
# from main or instantiate a Database() helper if shared. Since main.py has `db = Database()`, 
# let's instantiate a local module-level Database() or import it. To be completely modular 
# and independent of circular imports with main.py, we instantiate `db = Database()`.)
db = Database()

def get_utc_now() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

async def check_user_membership(bot, user_id: int) -> bool:
    """Checks if user has joined both mandatory channels."""
    channels = [REQUIRED_CHANNEL_1, REQUIRED_CHANNEL_2]
    for channel in channels:
        if not channel:
            continue
        try:
            chat_member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if chat_member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logger.error(f"Error checking membership for channel {channel} and user {user_id}: {e}")
            # If bot cannot check (e.g. not admin in channel), fail safe or treat as not joined
            return False
    return True

def get_force_join_keyboard() -> InlineKeyboardMarkup:
    """Generates inline keyboard for mandatory channel joins and refresh."""
    ch1_username = REQUIRED_CHANNEL_1.lstrip("@")
    ch2_username = REQUIRED_CHANNEL_2.lstrip("@")
    
    keyboard = InlineKeyboardMarkup(inline_router=[], inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel 1", url=f"https://t.me/{ch1_username}")],
        [InlineKeyboardButton(text="📢 Join Channel 2", url=f"https://t.me/{ch2_username}")],
        [InlineKeyboardButton(text="🔄 Check Again / Refresh", callback_data="check_force_join")]
    ])
    return keyboard

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Generates the main menu inline keyboard."""
    keyboard = InlineKeyboardMarkup(inline_router=[], inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Marketplace", callback_data="menu_marketplace"),
            InlineKeyboardButton(text="💼 Wallet", callback_data="menu_wallet")
        ],
        [
            InlineKeyboardButton(text="📦 My Orders", callback_data="menu_orders"),
            InlineKeyboardButton(text="👤 Profile", callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton(text="💬 Support", callback_data="menu_support")
        ]
    ])
    return keyboard

async def process_user_on_start(user_id: int, username: str, first_name: str) -> bool:
    """Handles user registration or update, and wallet creation if new. Returns is_banned status."""
    await db.connect()
    
    now = get_utc_now()
    
    # Check if user exists
    user_row = await db.fetchone("SELECT is_banned FROM users WHERE telegram_id = ?;", (user_id,))
    
    if user_row is None:
        # New user: Insert into users
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, join_date, last_activity, is_banned, total_orders)
            VALUES (?, ?, ?, ?, ?, 0, 0);
            """,
            (user_id, username, first_name, now, now)
        )
        # Create wallet automatically
        await db.execute(
            """
            INSERT INTO wallets (telegram_id, balance, total_deposit, total_withdraw, total_spent)
            VALUES (?, 0.0, 0.0, 0.0, 0.0);
            """,
            (user_id,)
        )
        logger.info(f"New user registered and wallet created: {user_id}")
        return False
    else:
        # Existing user: Update activity, username, first_name
        await db.execute(
            """
            UPDATE users 
            SET username = ?, first_name = ?, last_activity = ?
            WHERE telegram_id = ?;
            """,
            (username, first_name, now, user_id)
        )
        is_banned = bool(user_row["is_banned"])
        return is_banned

@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    """Handles the /start command."""
    user = message.from_user
    if not user:
        return

    user_id = user.id
    username = user.username
    first_name = user.first_name

    try:
        # 1. Database User & Wallet Check/Creation & Ban Check
        is_banned = await process_user_on_start(user_id, username, first_name)
        
        if is_banned:
            await message.answer(
                "❌ আপনার অ্যাকাউন্ট বর্তমানে নিষিদ্ধ।\nSupport-এর সাথে যোগাযোগ করুন।"
            )
            return

        # 2. Force Join Check
        is_joined = await check_user_membership(message.bot, user_id)
        if not is_joined:
            await message.answer(
                "⚠️ Bot ব্যবহার করতে হলে নিচের দুইটি Official Channel Join করুন।",
                reply_markup=get_force_join_keyboard()
            )
            return

        # 3. Welcome Message & Main Menu
        welcome_text = (
            f"স্বাগতম, <b>{first_name}</b>!\n\n"
            "এটি একটি নিরাপদ ও বিশ্বস্ত Digital Marketplace Bot। এখান থেকে আপনি সহজে বিভিন্ন ডিজিটাল পণ্য কিনতে পারবেন এবং আপনার ওয়ালেট ম্যানেজ করতে পারবেন।\n\n"
            "নিচের মেনু থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন:"
        )
        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logger.error(f"Error in /start handler for user {user_id}: {e}")
        await message.answer("⚠️ একটি প্রযুক্তিগত ত্রুটি ঘটেছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।")

@router.callback_query(F.data == "check_force_join")
async def callback_check_force_join(callback: CallbackQuery) -> None:
    """Handles the Force Join refresh check callback."""
    user = callback.from_user
    if not user:
        return

    user_id = user.id

    try:
        # Check if user is banned first
        await db.connect()
        user_row = await db.fetchone("SELECT is_banned FROM users WHERE telegram_id = ?;", (user_id,))
        if user_row and user_row["is_banned"]:
            await callback.answer("আপনার অ্যাকাউন্ট বর্তমানে নিষিদ্ধ।", show_alert=True)
            return

        is_joined = await check_user_membership(callback.bot, user_id)
        if not is_joined:
            await callback.answer(
                "❌ আপনি এখনো সবগুলো চ্যানেল Join করেন নাই! অনুগ্রহ করে Join করুন।",
                show_alert=True
            )
            return

        # If joined successfully, show main menu
        welcome_text = (
            f"ধন্যবাদ চ্যানেলগুলোতে জয়েন করার জন্য!\n\n"
            "এটি একটি নিরাপদ ও বিশ্বস্ত Digital Marketplace Bot।\n"
            "নিচের মেনু থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন:"
        )
        
        try:
            await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
            
        await callback.answer("✅ সফলভাবে ভেরিফাই হয়েছে!")

    except Exception as e:
        logger.error(f"Error in check_force_join callback for user {user_id}: {e}")
        await callback.answer("⚠️ ত্রুটি ঘটেছে। আবার চেষ্টা করুন।", show_alert=True)
        
