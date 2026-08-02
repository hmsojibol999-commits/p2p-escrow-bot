from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from keyboards.inline import InlineKeyboards
from keyboards.reply import ReplyKeyboards


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, db_session: AsyncSession) -> None:
    """
    Handles the /start command, greets the user, checks referral links,
    and displays the main dashboard.
    """
    first_name = db_user.first_name or "Valued User"
    
    welcome_text = (
        f"👋 **Welcome to Telegram Marketplace, {first_name}!**\n\n"
        f"Your ultimate, secure decentralized peer-to-peer digital marketplace.\n"
        f"• Buy & sell digital assets safely with **Escrow Protection**.\n"
        f"• Manage local and crypto balances with instant settlements.\n\n"
        f"Please choose an option from the menu below to get started:"
    )

    await message.answer(
        welcome_text,
        reply_markup=InlineKeyboards.get_main_menu_keyboard(is_admin=db_user.is_admin),
        parse_mode="Markdown"
    )
    
    # Send persistent reply keyboard for bottom bar navigation
    await message.answer(
        "📍 Navigation bar activated:",
        reply_markup=ReplyKeyboards.get_main_reply_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, db_user: User) -> None:
    """
    Returns the user to the main menu dashboard via inline button click.
    """
    first_name = db_user.first_name or "Valued User"

    menu_text = (
        f"🏠 **Main Menu - Dashboard**\n\n"
        f"Welcome back, {first_name}. What would you like to do today?"
    )

    await callback.message.edit_text(
        menu_text,
        reply_markup=InlineKeyboards.get_main_menu_keyboard(is_admin=db_user.is_admin),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(F.text == "🏠 Main Menu")
async def reply_main_menu(message: Message, db_user: User) -> None:
    """
    Returns the user to the main menu via persistent reply keyboard.
    """
    first_name = db_user.first_name or "Valued User"

    menu_text = (
        f"🏠 **Main Menu - Dashboard**\n\n"
        f"Welcome back, {first_name}. Choose an option below:"
    )

    await message.answer(
        menu_text,
        reply_markup=InlineKeyboards.get_main_menu_keyboard(is_admin=db_user.is_admin),
        parse_mode="Markdown"
    )
  
