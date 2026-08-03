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
from telethon_client import connect_client, disconnect_client
from favorites_handlers import (
    list_favorites_handler,
    get_favorites_conversation_handler,
    get_remove_favorite_conversation_handler,
)
from search_handlers import get_search_conversation_handler

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
        "Welcome to your <b>Telegram Productivity Bot</b>.\n"
        "Manage your favorite chats/channels and perform quick global searches seamlessly.\n\n"
        "Please select an option below:"
    )

    keyboard = [
        [
            InlineKeyboardButton("⭐ Favorites", callback_data="btn_favorites"),
            InlineKeyboardButton("🔍 Search Telegram", callback_data="btn_search"),
        ],
        [
            InlineKeyboardButton("➕ Add Favorite", callback_data="btn_add_fav"),
            InlineKeyboardButton("❌ Remove Favorite", callback_data="btn_remove_fav"),
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
            # If message content is identical, edit_text might raise an exception, fallback to sending new message
            await update.callback_query.message.reply_text(
                welcome_text, reply_markup=reply_markup, parse_mode="HTML"
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays information about the bot features and usage."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    help_text = (
        "ℹ️ <b>Telegram Productivity Bot Help</b>\n\n"
        "Here is what you can do with this bot:\n\n"
        "• <b>⭐ Favorites:</b> View all your saved favorite users, groups, channels, or bots.\n"
        "• <b>➕ Add Favorite:</b> Save a new entity by providing a custom title, username/link, and type.\n"
        "• <b>❌ Remove Favorite:</b> Delete an existing favorite using its title or username.\n"
        "• <b>🔍 Search Telegram:</b> Globally search public Telegram users, groups, and channels instantly.\n\n"
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

    if data == "btn_favorites":
        await list_favorites_handler(update, context)
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

async def post_init(application) -> None:
    """Actions to perform right after the bot application starts up (e.g., connecting Telethon)."""
    logger.info("Bot application starting up. Initializing Telethon client...")
    try:
        await connect_client()
        logger.info("Telethon client connected successfully during startup.")
    except Exception as e:
        logger.error(f"Failed to connect Telethon client on startup: {e}", exc_info=True)

async def post_shutdown(application) -> None:
    """Actions to perform right before the bot application shuts down (e.g., disconnecting Telethon)."""
    logger.info("Bot application shutting down. Disconnecting Telethon client...")
    try:
        await disconnect_client()
        logger.info("Telethon client disconnected gracefully.")
    except Exception as e:
        logger.error(f"Error during Telethon client shutdown: {e}", exc_info=True)

def main() -> None:
    """Initializes and runs the fully integrated Telegram productivity bot."""
    token = Config.BOT_TOKEN
    if not token:
        logger.error("BOT_TOKEN is missing in configuration. Exiting application.")
        sys.exit(1)

    # Build python-telegram-bot application with lifecycle hooks
    application = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Register conversation handlers for complex flows (Add Favorite, Remove Favorite, Search)
    application.add_handler(get_favorites_conversation_handler())
    application.add_handler(get_remove_favorite_conversation_handler())
    application.add_handler(get_search_conversation_handler())

    # Register general callback router for non-conversation buttons (Favorites list, Help, Back to Menu)
    application.add_handler(CallbackQueryHandler(button_callback_router, pattern="^(btn_favorites|btn_help|btn_back_menu)$"))

    # Register global error handler
    application.add_handler(object) # standard registration placeholder or built-in add_error_handler
    application.add_error_handler(global_error_handler)

    # Start polling mode (ideal for Render long-polling deployments)
    logger.info("Starting bot application polling loop...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
