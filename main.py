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
from favorites_handlers import (
    list_favorites_handler,
    get_favorites_conversation_handler,
    get_remove_favorite_conversation_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} started the bot.")

    welcome_text = (
        f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
        "Welcome to your Telegram Favorites Productivity Bot.\n"
        "Manage your favorite chats, channels, and bots easily.\n\n"
        "Please select an option below:"
    )

    keyboard = [
        [
            InlineKeyboardButton("⭐ Favorites", callback_data="btn_favorites"),
            InlineKeyboardButton("➕ Add Favorite", callback_data="btn_add_fav"),
        ],
        [
            InlineKeyboardButton("❌ Remove Favorite", callback_data="btn_remove_fav"),
            InlineKeyboardButton("ℹ️ Help", callback_data="btn_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    help_text = (
        "ℹ️ <b>Bot Help</b>\n\n"
        "• <b>⭐ Favorites:</b> View your saved favorites.\n"
        "• <b>➕ Add Favorite:</b> Save a new favorite entity.\n"
        "• <b>❌ Remove Favorite:</b> Delete an existing favorite.\n\n"
        "<i>Use /start to return to the main menu.</i>"
    )

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await message_func(help_text, reply_markup=reply_markup, parse_mode="HTML")

async def button_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    logger.error("Exception while handling an update:", exc_info=context.error)

def main() -> None:
    token = Config.BOT_TOKEN
    if not token:
        logger.error("BOT_TOKEN is missing. Exiting.")
        sys.exit(1)

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(get_favorites_conversation_handler())
    application.add_handler(get_remove_favorite_conversation_handler())
    application.add_handler(CallbackQueryHandler(button_callback_router, pattern="^(btn_favorites|btn_help|btn_back_menu)$"))

    application.add_error_handler(global_error_handler)

    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
