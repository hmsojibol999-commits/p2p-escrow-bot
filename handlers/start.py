import logging
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from config import REQUIRED_CHANNEL_1, REQUIRED_CHANNEL_2
from database import Database

logger = logging.getLogger(__name__)
router = Router()
db = Database()

def get_utc_now() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

async def check_user_membership(bot, user_id: int) -> bool:
    """Checks if the user has joined both mandatory official channels."""
    channels = [REQUIRED_CHANNEL_1, REQUIRED_CHANNEL_2]
    for channel in channels:
        if not channel:
            continue
        try:
            chat_member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if chat_member.status in ["left", "kicked"]:
                logger.info(f"Channel verification failed: User {user_id} has not joined channel {channel}")
                return False
        except TelegramAPIError as e:
            logger.error(f"Telegram API Error checking membership for channel {channel} and user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking membership for channel {channel} and user {user_id}: {e}")
            return False
    
    logger.info(f"Channel verification passed for user {user_id}")
    return True

def get_force_join_keyboard() -> InlineKeyboardMarkup:
    """Generates inline keyboard for mandatory channel joins and refresh check."""
    ch1_username = REQUIRED_CHANNEL_1.lstrip("@")
    ch2_username = REQUIRED_CHANNEL_2.lstrip("@")
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel 1", url=f"https://t.me/{ch1_username}")],
        [InlineKeyboardButton(text="📢 Join Channel 2", url=f"https://t.me/{ch2_username}")],
        [InlineKeyboardButton(text="🔄 Check Again", callback_data="check_force_join")]
    ])

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Generates the professional main menu inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
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

async def register_or_update_user(user_id: int, username: str, first_name: str) -> None:
    """Registers new user with wallets/defaults or updates activity and info for existing users."""
    await db.connect()
    now = get_utc_now()
    
    user_row = await db.fetchone("SELECT telegram_id FROM users WHERE telegram_id = ?;", (user_id,))
    
    if user_row is None:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, join_date, last_activity, is_banned, total_orders)
            VALUES (?, ?, ?, ?, ?, 0, 0);
            """,
            (user_id, username, first_name, now, now)
        )
        await db.execute(
            """
            INSERT INTO wallets (telegram_id, balance, total_deposit, total_withdraw, total_spent)
            VALUES (?, 0.0, 0.0, 0.0, 0.0);
            """,
            (user_id,)
        )
        logger.info(f"New User Registered: ID {user_id}, Username: @{username}")
    else:
        await db.execute(
            """
            UPDATE users 
            SET username = ?, first_name = ?, last_activity = ?
            WHERE telegram_id = ?;
            """,
            (username, first_name, now, user_id)
        )
        logger.info(f"Existing User Started: ID {user_id}, Username: @{username}")

@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    """Handles the /start command, registers/updates user, performs channel verification, and shows menu."""
    user = message.from_user
    if not user:
        return

    user_id = user.id
    username = user.username or "No Username"
    first_name = user.first_name

    logger.info(f"Bot Started by User ID: {user_id}")

    try:
        await register_or_update_user(user_id, username, first_name)

        is_joined = await check_user_membership(message.bot, user_id)
        if not is_joined:
            text = (
                f"👋 স্বাগতম, <b>{first_name}</b>!\n\n"
                "এই Bot ব্যবহার করার আগে অনুগ্রহ করে নিচের দুটি Official Channel Join করুন:"
            )
            await message.answer(text, reply_markup=get_force_join_keyboard())
            return

        welcome_text = (
            f"স্বাগতম, <b>{first_name}</b>!\n\n"
            "আপনার প্রয়োজনীয় সেবা নিচের Menu থেকে নির্বাচন করুন:"
        )
        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logger.error(f"Unexpected error in cmd_start for user {user_id}: {e}")
        try:
            await message.answer("⚠️ একটি প্রযুক্তিগত ত্রুটি ঘটেছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
        except Exception:
            pass

@router.callback_query(F.data == "check_force_join")
async def callback_check_force_join(callback: CallbackQuery) -> None:
    """Handles callback for checking mandatory channel memberships again."""
    user = callback.from_user
    if not user:
        return

    user_id = user.id
    first_name = user.first_name

    try:
        is_joined = await check_user_membership(callback.bot, user_id)
        if not is_joined:
            await callback.answer("আপনি এখনও সব Channel Join করেননি!", show_alert=True)
            return

        welcome_text = (
            f"স্বাগতম, <b>{first_name}</b>!\n\n"
            "আপনার প্রয়োজনীয় সেবা নিচের Menu থেকে নির্বাচন করুন:"
        )
        
        try:
            await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
            
        await callback.answer("✅ চ্যানেল ভেরিফিকেশন সফল হয়েছে!")

    except Exception as e:
        logger.error(f"Unexpected error in callback_check_force_join for user {user_id}: {e}")
        await callback.answer("⚠️ ত্রুটি ঘটেছে। আবার চেষ্টা করুন।", show_alert=True)

@router.callback_query(F.data == "menu_main")
async def callback_return_main_menu(callback: CallbackQuery) -> None:
    """Handles returning to the main menu from submenus with re-verification of force join."""
    user = callback.from_user
    if not user:
        return

    user_id = user.id
    first_name = user.first_name

    try:
        is_joined = await check_user_membership(callback.bot, user_id)
        if not is_joined:
            text = (
                f"👋 স্বাগতম, <b>{first_name}</b>!\n\n"
                "এই Bot ব্যবহার করতে হলে অনুগ্রহ করে নিচের দুটি Official Channel Join করুন:"
            )
            try:
                await callback.message.edit_text(text, reply_markup=get_force_join_keyboard())
            except TelegramBadRequest:
                await callback.message.answer(text, reply_markup=get_force_join_keyboard())
            await callback.answer("⚠️ অনুগ্রহ করে চ্যানেলগুলোতে জয়েন করুন।", show_alert=True)
            return

        welcome_text = (
            f"স্বাগতম, <b>{first_name}</b>!\n\n"
            "আপনার প্রয়োজনীয় সেবা নিচের Menu থেকে নির্বাচন করুন:"
        )
        
        try:
            await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard())
        except TelegramBadRequest:
            await callback.message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
            
        await callback.answer()

    except Exception as e:
        logger.error(f"Unexpected error returning to main menu for user {user_id}: {e}")
        await callback.answer("⚠️ ত্রুটি ঘটেছে।", show_alert=True)
        
