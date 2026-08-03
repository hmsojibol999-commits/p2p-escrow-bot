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
from favorites import (
    get_favorites,
    add_favorite,
    search_favorites,
    delete_favorite,
)
from utils import format_favorite

# Configure logging
logger = logging.getLogger(__name__)

# Conversation States for Add Favorite
ADD_TITLE, ADD_IDENTIFIER, ADD_TYPE = range(3)

# Conversation States for Search Favorites
SEARCH_KEYWORD = 3

# Conversation States for Remove Favorite
REMOVE_KEY = 4

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command and displays the main interactive menu."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot.")

    welcome_text = (
        f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
        "Welcome to your <b>Telegram Favorites Bot</b>.\n"
        "Easily save and manage your favorite users, groups, channels, and bots.\n\n"
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
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            await query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays help information about the bot features."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    help_text = (
        "ℹ️ <b>Bot Help & Guide</b>\n\n"
        "Here is what you can do:\n\n"
        "• <b>⭐ View Favorites:</b> See all your saved entities.\n"
        "• <b>➕ Add Favorite:</b> Save a new user, group, channel, or bot step by step.\n"
        "• <b>🔍 Search Favorites:</b> Search through your saved favorites by keyword.\n"
        "• <b>❌ Remove Favorite:</b> Delete a saved item using its title or username.\n\n"
        "<i>Type /cancel at any time during a conversation to abort.</i>"
    )

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await message_func(help_text, reply_markup=reply_markup, parse_mode="HTML")

# --- VIEW FAVORITES HANDLER ---

async def view_favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays all saved favorites or 'No favorites found.' if empty."""
    query = update.callback_query
    await query.answer()

    favorites = await get_favorites()

    if not favorites:
        text = "⭐ <b>Your Favorites</b>\n\nNo favorites found."
    else:
        text = "⭐ <b>Your Saved Favorites:</b>\n\n"
        for fav in favorites:
            text += f"{format_favorite(fav)}\n\n"

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

# --- ADD FAVORITE CONVERSATION ---

async def start_add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: Ask for title."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    await message_func(
        "➕ <b>Add Favorite</b> (Step 1/3)\n\n"
        "Please enter a custom <b>Title</b> for this favorite (e.g., 'My Favorite Group'):\n\n"
        "<i>(Type /cancel to abort)</i>",
        parse_mode="HTML"
    )
    return ADD_TITLE

async def add_receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: Receive title and ask for identifier (username/link)."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("Title cannot be empty. Please enter a valid title:")
        return ADD_TITLE

    context.user_data["add_title"] = title
    await update.message.reply_text(
        f"✅ Title: <b>{title}</b>\n\n"
        "➕ <b>Add Favorite</b> (Step 2/3)\n\n"
        "Now, send the <b>Username</b> (e.g., <code>@example</code>) or <b>t.me Link</b> (e.g., <code>https://t.me/example</code>):",
        parse_mode="HTML"
    )
    return ADD_IDENTIFIER

async def add_receive_identifier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 3: Receive identifier and ask for type."""
    identifier = update.message.text.strip()
    if not identifier:
        await update.message.reply_text("Identifier cannot be empty. Please enter a valid username or link:")
        return ADD_IDENTIFIER

    context.user_data["add_identifier"] = identifier

    keyboard = [
        [
            InlineKeyboardButton("User", callback_data="type_user"),
            InlineKeyboardButton("Group", callback_data="type_group"),
        ],
        [
            InlineKeyboardButton("Channel", callback_data="type_channel"),
            InlineKeyboardButton("Bot", callback_data="type_bot"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "➕ <b>Add Favorite</b> (Step 3/3)\n\n"
        "Select the <b>Type</b> of this entity:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return ADD_TYPE

async def add_receive_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Final Step: Receive type, save to storage, and complete conversation."""
    query = update.callback_query
    await query.answer()

    fav_type = query.data.replace("type_", "")
    title = context.user_data.get("add_title")
    identifier = context.user_data.get("add_identifier")

    result = await add_favorite(title, identifier, fav_type)

    if result.get("success"):
        response_text = f"🎉 {result.get('message')}"
    else:
        response_text = f"❌ Error: {result.get('message')}"

    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("⭐ View Favorites", callback_data="btn_view_favorites")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(response_text, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

# --- SEARCH FAVORITES CONVERSATION ---

async def start_search_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates search conversation."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    await message_func(
        "🔍 <b>Search Favorites</b>\n\n"
        "Please enter a keyword to search by title or username:\n\n"
        "<i>(Type /cancel to abort)</i>",
        parse_mode="HTML"
    )
    return SEARCH_KEYWORD

async def receive_search_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes search keyword and displays results."""
    keyword = update.message.text.strip()
    if not keyword:
        await update.message.reply_text("Search keyword cannot be empty. Please enter a valid keyword:")
        return SEARCH_KEYWORD

    results = await search_favorites(keyword)

    if not results:
        text = f"🔍 <b>Search Results for '{keyword}'</b>\n\nNo favorites found matching your query."
    else:
        text = f"🔍 <b>Search Results for '{keyword}':</b>\n\n"
        for fav in results:
            text += f"{format_favorite(fav)}\n\n"

    keyboard = [
        [InlineKeyboardButton("🔍 Search Again", callback_data="btn_search_favorites")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

# --- REMOVE FAVORITE CONVERSATION ---

async def start_remove_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates removal conversation."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    await message_func(
        "❌ <b>Remove Favorite</b>\n\n"
        "Please enter the exact <b>Title</b> or <b>Username/Link</b> of the favorite you want to remove:\n\n"
        "<i>(Type /cancel to abort)</i>",
        parse_mode="HTML"
    )
    return REMOVE_KEY

async def receive_remove_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes removal and displays status."""
    key = update.message.text.strip()
    if not key:
        await update.message.reply_text("Key cannot be empty. Please enter a valid title or username:")
        return REMOVE_KEY

    result = await delete_favorite(key)

    if result.get("success"):
        response_text = f"🗑️ {result.get('message')}"
    else:
        response_text = f"❌ Error: {result.get('message')}"

    keyboard = [
        [InlineKeyboardButton("⭐ View Favorites", callback_data="btn_view_favorites")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

# --- CANCEL HANDLER ---

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels any active conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "🚫 Action cancelled.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
        )
    )
    return ConversationHandler.END

# --- ROUTER & HANDLER BUILDERS ---

async def button_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Routes non-conversation button clicks."""
    query = update.callback_query
    data = query.data

    if data == "btn_view_favorites":
        await view_favorites_handler(update, context)
    elif data == "btn_help":
        await help_command(update, context)
    elif data == "btn_back_menu":
        await start_command(update, context)
    else:
        await query.answer()

def get_handlers() -> list:
    """Returns all command, conversation, and callback handlers for main.py integration."""
    
    add_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_favorite, pattern="^btn_add_favorite$")],
        states={
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_receive_title)],
            ADD_IDENTIFIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_receive_identifier)],
            ADD_TYPE: [CallbackQueryHandler(add_receive_type, pattern="^type_(user|group|channel|bot)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )

    search_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_search_favorites, pattern="^btn_search_favorites$")],
        states={
            SEARCH_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_keyword)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )

    remove_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_favorite, pattern="^btn_remove_favorite$")],
        states={
            REMOVE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_key)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )

    general_callback_handler = CallbackQueryHandler(
        button_callback_router,
        pattern="^(btn_view_favorites|btn_help|btn_back_menu)$"
    )

    return 
