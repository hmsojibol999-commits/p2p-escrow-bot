import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from search import search_telegram

# Configure logging
logger = logging.getLogger(__name__)

# Conversation State for Search
SEARCH_QUERY = 0

async def start_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the search conversation flow when the search button is clicked."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    await message_func(
        "🔍 <b>Telegram Public Search</b>\n\n"
        "Please enter a keyword to search for a public Telegram User, Group, or Channel.\n\n"
        "<i>(Type /cancel at any time to abort)</i>",
        parse_mode="HTML"
    )
    return SEARCH_QUERY

async def receive_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the keyword, calls search.py, and displays results."""
    keyword = update.message.text.strip()
    
    if not keyword:
        await update.message.reply_text("Search keyword cannot be empty. Please enter a valid keyword:")
        return SEARCH_QUERY

    await update.message.reply_text(f"⏳ Searching for <b>{keyword}</b>...", parse_mode="HTML")

    # Call search function from search.py
    search_response = await search_telegram(keyword, limit=10)

    if not search_response.get("success"):
        error_msg = search_response.get("message", "An unknown error occurred during search.")
        await update.message.reply_text(
            f"❌ <b>Search Failed</b>\n\n{error_msg}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
            ),
            parse_mode="HTML"
        )
        return ConversationHandler.END

    results = search_response.get("results", [])

    if not results:
        response_text = f"🔍 <b>Search Results for '{keyword}'</b>\n\nNo results found."
    else:
        response_text = f"🔍 <b>Top Results for '{keyword}':</b>\n\n"
        for idx, item in enumerate(results, 1):
            title = item.get("title", "N/A")
            username = item.get("username")
            item_type = item.get("type", "unknown").upper()
            tme_link = item.get("tme_link")

            response_text += f"{idx}. <b>{title}</b> ({item_type})\n"
            if username:
                if tme_link:
                    response_text += f"   🔗 <a href='{tme_link}'>{username}</a>\n"
                else:
                    response_text += f"   🔗 <code>{username}</code>\n"
            response_text += "\n"

    keyboard = [
        [InlineKeyboardButton("🔍 Search Again", callback_data="btn_search")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        response_text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    return ConversationHandler.END

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the active search conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "🚫 Search cancelled.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
        )
    )
    return ConversationHandler.END

def get_search_conversation_handler() -> ConversationHandler:
    """Returns the ConversationHandler for the search feature."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_search_handler, pattern="^btn_search$")
        ],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_query)]
        },
        fallbacks=[CommandHandler("cancel", cancel_search)]
      )
  
