import logging
import re
import sys
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from config import Config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# In-memory storage: user_id -> list of links
user_links: Dict[int, List[str]] = {}

# Conversation state
ADD_LINK = 0

def validate_link(value: str) -> bool:
    """Validates if the input is a valid Telegram link or username."""
    if not isinstance(value, str):
        return False
    value = value.strip()
    
    # Patterns for t.me links (standard, invite links, private group/channel chat links, usernames)
    patterns = [
        r"^(?:https?://)?(?:t\.me)/[a-zA-Z0-9_]{5,32}$",       # Standard username link
        r"^(?:https?://)?(?:t\.me)/\+[a-zA-Z0-9_-]+$",         # Invite link
        r"^(?:https?://)?(?:t\.me)/c/\d+/\d+$",                # Private chat message link
        r"^@?[a-zA-Z0-9_]{5,32}$"                              # Bare username or @username
    ]
    
    return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)

def normalize_link(value: str) -> str:
    """Normalizes the input link to a proper clickable format if possible."""
    value = value.strip()
    if value.startswith("@"):
        return f"https://t.me/{value[1:]}"
    if not value.startswith("http://") and not value.startswith("https://"):
        if value.startswith("t.me/"):
            return f"https://{value}"
        elif re.match(r"^[a-zA-Z0-9_]{5,32}$", value):
            return f"https://t.me/{value}"
    return value

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command and displays the main menu."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot.")

    welcome_text = (
        f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
        "Save your important Telegram links and access them instantly via buttons.\n\n"
        "Choose an option below:"
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Link", callback_data="btn_add_link"),
            InlineKeyboardButton("📂 My Links", callback_data="btn_my_links"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def start_add_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the process of adding a link."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "➕ <b>Add Telegram Link</b>\n\n"
        "Please send the Telegram link or username (e.g., <code>https://t.me/example</code> or <code>@username</code>):\n\n"
        "<i>(Type /cancel to abort)</i>",
        parse_mode="HTML"
    )
    return ADD_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives, validates, and stores the link in memory."""
    user_id = update.effective_user.id
    raw_input = update.message.text.strip()

    if not validate_link(raw_input):
        await update.message.reply_text(
            "❌ Invalid Telegram link or username format. Please try again or type /cancel:"
        )
        return ADD_LINK

    normalized = normalize_link(raw_input)

    # Initialize user storage if not present
    if user_id not in user_links:
        user_links[user_id] = []

    # Check limit (max 50 links)
    if len(user_links[user_id]) >= 50:
        await update.message.reply_text(
            "⚠️ You have reached the maximum limit of 50 saved links.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]])
        )
        return ConversationHandler.END

    # Check duplicate
    if normalized in user_links[user_id]:
        await update.message.reply_text(
            "⚠️ This link is already in your saved list!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]])
        )
        return ConversationHandler.END

    user_links[user_id].append(normalized)
    logger.info(f"User {user_id} saved link: {normalized}")

    keyboard = [
        [InlineKeyboardButton("📂 View My Links", callback_data="btn_my_links")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Successfully saved!\n🔗 <code>{normalized}</code>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return ConversationHandler.END

async def my_links_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays all saved links as inline URL buttons."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    links = user_links.get(user_id, [])

    if not links:
        text = "📂 <b>My Saved Links</b>\n\nNo links saved yet."
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
    else:
        text = f"📂 <b>My Saved Links ({len(links)}/50):</b>\n\nClick any button below to open the link:"
        keyboard = []
        for link in links:
            # Extract a clean display label from the link
            label = link.replace("https://t.me/", "").replace("http://t.me/", "").strip("/")
            keyboard.append([InlineKeyboardButton(f"🔗 {label}", url=link)])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation."""
    await update.message.reply_text(
        "🚫 Action cancelled.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]])
    )
    return ConversationHandler.END

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler."""
    logger.error("Exception while handling an update:", exc_info=context.error)

def main() -> None:
    """Initializes and runs the bot."""
    token = Config.BOT_TOKEN
    if not token:
        logger.error("BOT_TOKEN is missing. Exiting application.")
        sys.exit(1)

    application = ApplicationBuilder().token(token).build()

    # Conversation handler for adding links
    add_link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_link, pattern="^btn_add_link$")],
        states={
            ADD_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(add_link_conv)
    application.add_handler(CallbackQueryHandler(my_links_callback, pattern="^btn_my_links$"))
    application.add_handler(CallbackQueryHandler(start_command, pattern="^btn_back_menu$"))
    
    application.add_error_handler(global_error_handler)

    print("Bot Started Successfully")
    logger.info("Starting bot polling loop...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
