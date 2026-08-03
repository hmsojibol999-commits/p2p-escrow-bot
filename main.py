import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import Config
from favorites import get_favorites
from utils import format_favorite
# handlers.py থেকে হ্যান্ডলারগুলো ইমপোর্ট করা হচ্ছে
from handlers import (
    get_add_favorite_conversation_handler,
    get_remove_favorite_conversation_handler,
    get_search_favorites_conversation_handler,
)

# Configure comprehensive logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command and displays the main interactive productivity menu."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) accessed the main menu via /start.")

    welcome_text = (
        f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
        "Welcome to your <b>Telegram Favorites Productivity Bot</b>.\n"
        "Manage and organize your favorite users, groups, channels, and bots easily.\n\n"
        "Please select an option below:"
    )

    keyboard = [
        [
            InlineKeyboardButton("⭐ View Favorites", callback_data="btn_view_favorites"),
            InlineKeyboardButton("➕ Add Favorite", callback_data="btn_add_favorite"),
        ],
        [
            InlineKeyboardButton("🔍 Search Favorites", callback_data="btn_search_favorites"),
            InlineKeyboardButton("❌ Remove Favorite", callback_data="btn_remove_favorite"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="btn_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup, parse_mode="HTML"
        )
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                welcome_text, reply_markup=reply_markup, parse_mode="HTML"
            )
        except Exception:
            await update.callback_query.message.reply_text(
                welcome_text, reply_markup=reply_markup, parse_mode="HTML"
            )

async def view_favorites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays all saved favorites."""
    query = update.callback_query
    await query.answer()

    favorites = await get_favorites()

    if not favorites:
        text = "⭐ <b>Your Favorites</b>\n\nNo favorites found yet."
    else:
        text = "⭐ <b>Your Saved Favorites:</b>\n\n"
        for idx, fav in enumerate(favorites, 1):
            formatted_item = format_favorite(fav)
            text += f"<b>{idx}.</b>\n{formatted_item}\n\n"

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Favorite", callback_data="btn_add_favorite"),
            InlineKeyboardButton("❌ Remove Favorite", callback_data="btn_remove_favorite"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays information about the bot features and usage."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    help_text = (
        "ℹ️ <b>Telegram Favorites Bot Help</b>\n\n"
        "Here is what you can do with this bot:\n\n"
        "• <b>⭐ View Favorites:</b> View all your saved favorite users, groups, channels, or bots.\n"
        "• <b>➕ Add Favorite:</b> Save a new entity with a title, username/link, and type.\n"
        "• <b>🔍 Search Favorites:</b> Search through your saved favorites by keyword.\n"
        "• <b>❌ Remove Favorite:</b> Delete an existing favorite using its title or username.\n\n"
        "<i>Use /start to return to the main menu anytime.</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await message_func(help_text, reply_markup=reply_markup, parse_mode="HTML")

async def button_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Routes inline button callbacks that are not handled by conversation handlers."""
    query = update.callback_query
    data = query.data

    if data == "btn_view_favorites":
        await view_favorites_callback(update, context)
    elif data == "btn_help":
        await help_command(update, context)
    elif data == "btn_back_menu":
        await start_command(update, context)
    else:
        await query.answer()

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler to catch and log unhandled exceptions."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred while processing your request. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to send error notification to user: {e}")

def main() -> None:
    """Initializes and runs the Telegram favorites productivity bot."""
    token = Config.BOT_TOKEN
    if not token:
        logger.error("BOT_TOKEN is missing in configuration. Exiting application.")
        sys.exit(1)

    # Build python-telegram-bot application
    application = ApplicationBuilder().token(token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Register conversation handlers from handlers.py
    application.add_handler(get_add_favorite_conversation_handler())
    application.add_handler(get_remove_favorite_conversation_handler())
    application.add_handler(get_search_favorites_conversation_handler())

    # Register general callback router for non-conversation buttons
    application.add_handler(
        CallbackQueryHandler(
            button_callback_router,
            pattern="^(btn_view_favorites|btn_help|btn_back_menu)$"
        )
    )

    # Register global error handler
    application.add_error_handler(global_error_handler)

    # Startup Log Requirement
    print("Bot Started Successfully")
    logger.info("Bot application starting up and entering polling mode...")

    # Start polling mode (optimized for Render long-polling deployments)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
