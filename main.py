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

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command and displays a welcome message with an interactive inline keyboard."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot.")

    welcome_text = (
        f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
        "Welcome to your Telegram Productivity Bot.\n"
        "Manage your favorite chats/channels and perform quick searches seamlessly.\n\n"
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
        await update.callback_query.message.edit_text(
            welcome_text, reply_markup=reply_markup, parse_mode="HTML"
        )

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all inline keyboard button callback queries with respective placeholders."""
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Received callback query: {data} from user {query.from_user.id}")

    if data == "btn_favorites":
        response_text = "⭐ Favorites module coming next."
    elif data == "btn_search":
        response_text = "🔍 Search module coming next."
    elif data == "btn_add_fav":
        response_text = "➕ Add Favorite module coming next."
    elif data == "btn_remove_fav":
        response_text = "❌ Remove Favorite module coming next."
    elif data == "btn_help":
        response_text = "ℹ️ Help module coming next."
    else:
        response_text = "⚠️ Unknown action."

    # Back button to return to main menu
    back_keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
    )

    if data == "btn_back_menu":
        await start_command(update, context)
    else:
        # Update current message with the placeholder response and back button
        await query.message.edit_text(response_text, reply_markup=back_keyboard)

def main() -> None:
    """Initializes and starts the Telegram bot application."""
    token = Config.BOT_TOKEN
    if not token:
        logger.error("BOT_TOKEN is missing. Exiting application.")
        sys.exit(1)

    # Build application
    application = ApplicationBuilder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    # Start the bot (Polling mode ideal for development/Render webhook setups if configured)
    logger.info("Starting bot application in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
