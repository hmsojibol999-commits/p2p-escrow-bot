import logging
import re
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def validate_username(value: str) -> bool:
    """
    Validates a Telegram username.
    Accepts both '@username' and 'username' formats.
    
    Args:
        value (str): The username string to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    value = value.strip()
    # Telegram username rules: 5-32 characters, a-z, 0-9, underscores.
    # Can optionally start with '@'.
    pattern = r"^@?[a-zA-Z0-9_]{5,32}$"
    return bool(re.match(pattern, value))

def normalize_username(value: str) -> str:
    """
    Normalizes a username by stripping whitespace, removing leading '@', and converting to lowercase.
    
    Args:
        value (str): The username string.
        
    Returns:
        str: Normalized username or empty string if invalid.
    """
    if not isinstance(value, str):
        return ""
    try:
        cleaned = value.strip()
        if cleaned.startswith("@"):
            cleaned = cleaned[1:]
        return cleaned.lower()
    except Exception as e:
        logger.error(f"Error normalizing username '{value}': {e}", exc_info=True)
        return ""

def validate_tme_link(value: str) -> bool:
    """
    Validates Telegram t.me or telegram.me links.
    Accepts formats:
    - https://t.me/...
    - http://t.me/...
    - t.me/...
    - telegram.me/...
    
    Args:
        value (str): The link string to validate.
        
    Returns:
        bool: True if valid t.me link format, False otherwise.
    """
    if not isinstance(value, str):
        return False
    value = value.strip()
    pattern = r"^(?:https?://)?(?:t\.me|telegram\.me)/[a-zA-Z0-9_]{5,32}$"
    return bool(re.match(pattern, value, re.IGNORECASE))

def extract_username(value: str) -> Optional[str]:
    """
    Extracts the username from a Telegram link or username input.
    
    Example:
        https://t.me/example -> example
        @example -> example
        
    Args:
        value (str): Link or username string.
        
    Returns:
        Optional[str]: Extracted clean username, or None if extraction fails.
    """
    if not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value:
        return None

    try:
        # Try matching t.me / telegram.me format
        tme_match = re.match(r"^(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]{5,32})", value, re.IGNORECASE)
        if tme_match:
            return tme_match.group(1).lower()

        # Try matching direct username format (with or without @)
        if validate_username(value):
            return normalize_username(value)

        return None
    except Exception as e:
        logger.error(f"Error extracting username from '{value}': {e}", exc_info=True)
        return None

def format_search_result(item: Dict[str, Any]) -> str:
    """
    Formats a single search result dictionary into a clean, readable text block.
    
    Args:
        item (dict): Dictionary containing entity details (title, username, type, tme_link).
        
    Returns:
        str: Formatted string representation of the search result.
    """
    if not isinstance(item, dict):
        return "Invalid item format."

    try:
        title = item.get("title", "N/A")
        username = item.get("username")
        item_type = item.get("type", "unknown").upper()
        tme_link = item.get("tme_link")

        lines = [f"• <b>{title}</b> ({item_type})"]
        if username:
            if tme_link:
                lines.append(f"  🔗 <a href='{tme_link}'>{username}</a>")
            else:
                lines.append(f"  🔗 <code>{username}</code>")
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error formatting search result item: {e}", exc_info=True)
        return "Error displaying item."

def escape_markdown(text: str) -> str:
    """
    Escapes special characters for Telegram MarkdownV2 formatting.
    Characters to escape: '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'
    
    Args:
        text (str): The raw text string.
        
    Returns:
        str: Escaped text safe for MarkdownV2.
    """
    if not isinstance(text, str):
        return ""
    
    try:
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)
    except Exception as e:
        logger.error(f"Error escaping markdown text: {e}", exc_info=True)
        return text
        
