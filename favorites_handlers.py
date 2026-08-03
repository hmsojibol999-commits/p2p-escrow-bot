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
    delete_favorite,
    search_favorites,
)

# Configure logging
logger = logging.getLogger(__name__)

# Conversation States for Add Favorite
TITLE, IDENTIFIER, TYPE = range(3)

# Conversation States for Remove Favorite
REMOVE_KEY = 0

async def list_favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the list of saved favorites to the user."""
    query = update.callback_query
    if query:
        await query.answer()

    favorites = await get_favorites()

    if not favorites:
        text = "⭐ <b>Your Favorites</b>\n\nNo favorites found yet."
    else:
        text = "⭐ <b>Your Saved Favorites:</b>\n\n"
        for idx, fav in enumerate(favorites, 1):
            title = fav.get("title", "N/A")
            identifier = fav.get("identifier", "N/A")
            fav_type = fav.get("type", "unknown").upper()
            text += f"{idx}. <b>{title}</b> ({fav_type})\n   🔗 <code>{identifier}</code>\n\n"

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Favorite", callback_data="btn_add_fav"),
            InlineKeyboardButton("❌ Remove Favorite", callback_data="btn_remove_fav"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

# --- ADD FAVORITE CONVERSATION HANDLERS ---

async def start_add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the process of adding a new favorite."""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text

    await message_func(
        "➕ <b>Add New Favorite</b>\n\n"
        "Please enter a <b>Title</b> for this favorite (e.g., 'My Favorite Channel'):\n\n"
        "<i>(Type /cancel at any time to abort)</i>",
        parse_mode="HTML"
    )
    return TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives and stores the title, then asks for the username or link."""
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Title cannot be empty. Please enter a valid title:")
        return TITLE

    context.user_data["new_fav_title"] = text
    await update.message.reply_text(
        f"✅ Title: <b>{text}</b>\n\n"
        "Now, send the <b>Username</b> (e.g., <code>@username</code>) or <b>Telegram Link</b> (e.g., <code>https://t.me/username</code>):",
        parse_mode="HTML"
    )
    return IDENTIFIER

async def receive_identifier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives and stores the identifier, then asks for the entity type."""
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Identifier cannot be empty. Please enter a valid username or link:")
        return IDENTIFIER

    context.user_data["new_fav_identifier"] = text

    # Keyboard for choosing type
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
        "Select the <b>Type</b> of this entity:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return TYPE

async def receive_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the type via inline button, saves the favorite, and ends conversation."""
    query = update.callback_query
    await query.answer()

    data = query.data
    fav_type = data.replace("type_", "")

    title = context.user_data.get("new_fav_title")
    identifier = context.user_data.get("new_fav_identifier")

    # Call favorites.py function to save
    result = await add_favorite(title, identifier, fav_type)

    if result.get("success"):
        response_text = f"🎉 {result.get('message')}"
    else:
        response_text = f"❌ Error: {result.get('message')}"

    # Clear user data cache
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("⭐ View Favorites", callback_data="btn_favorites")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(response_text, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

# --- REMOVE FAVORITE CONVERSATION HANDLERS ---

async def start_remove_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the process of removing a favorite."""
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
    """Processes the removal key and updates storage."""
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
        [InlineKeyboardButton("⭐ View Favorites", callback_data="btn_favorites")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current active conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "🚫 Action cancelled.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back_menu")]]
        )
    )
    return ConversationHandler.END

def get_favorites_conversation_handler() -> ConversationHandler:
    """Returns the ConversationHandler for adding favorites."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_favorite, pattern="^btn_add_fav$")
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            IDENTIFIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_identifier)],
            TYPE: [CallbackQueryHandler(receive_type_callback, pattern="^type_(user|group|channel|bot)$")]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )

def get_remove_favorite_conversation_handler() -> ConversationHandler:
    """Returns the ConversationHandler for removing favorites."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_remove_favorite, pattern="^btn_remove_fav$")
        ],
        states={
            REMOVE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_remove_key)]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
  )
  
