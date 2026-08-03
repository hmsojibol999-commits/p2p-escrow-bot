import logging
import re
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def normalize_username(value: str) -> str:
    """
    Normalizes a Telegram username or link input by stripping whitespace,
    removing leading '@', and converting to lowercase.
    
    Args:
        value (str): The username or handle string.
        
    Returns:
        str: Normalized clean username string or empty string on failure.
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

def validate_username(value: str) -> bool:
    """
    Validates a Telegram username based on official Telegram rules:
    - 5 to 32 characters long.
    - Can contain Latin letters, numbers, and underscores.
    - Can optionally start with '@'.
    
    Args:
        value (str): The username string to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    try:
        value = value.strip()
        pattern = r"^@?[a-zA-Z0-9_]{5,32}$"
        return bool(re.match(pattern, value))
    except Exception as e:
        logger.error(f"Error validating username '{value}': {e}", exc_info=True)
        return False

def validate_tme_link(value: str) -> bool:
    """
    Validates Telegram t.me links.
    Accepts formats:
    - https://t.me/...
    - http://t.me/...
    - t.me/...
    
    Args:
        value (str): The link string to validate.
        
    Returns:
        bool: True if valid t.me link format, False otherwise.
    """
    if not isinstance(value, str):
        return False
    try:
        value = value.strip()
        pattern = r"^(?:https?://)?(?:t\.me)/[a-zA-Z0-9_]{5,32}$"
        return bool(re.match(pattern, value, re.IGNORECASE))
    except Exception as e:
        logger.error(f"Error validating t.me link '{value}': {e}", exc_info=True)
        return False

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
    
    try:
        value = value.strip()
        if not value:
            return None

        # Check for t.me link
        tme_match = re.match(r"^(?:https?://)?(?:t\.me)/([a-zA-Z0-9_]{5,32})", value, re.IGNORECASE)
        if tme_match:
            return tme_match.group(1).lower()

        # Check for direct username
        if validate_username(value):
            return normalize_username(value)

        return None
    except Exception as e:
        logger.error(f"Error extracting username from '{value}': {e}", exc_info=True)
        return None

def format_favorite(item: Dict[str, Any]) -> str:
    """
    Formats a single favorite dictionary item into a clean, readable text block.
    
    Example output:
        ⭐ My Friend
        👤 User
        🔗 @example
        
    Args:
        item (dict): Dictionary containing favorite details (title, identifier, type).
        
    Returns:
        str: Formatted string representation of the favorite item.
    """
    if not isinstance(item, dict):
        return "Invalid favorite item format."

    try:
        title = item.get("title", "N/A")
        identifier = item.get("identifier", "N/A")
        fav_type = item.get("type", "user").lower()

        # Map type to appropriate emoji/label
        type_mapping = {
            "user": "👤 User",
            "group": "👥 Group",
            "channel": "📢 Channel",
            "bot": "🤖 Bot"
        }
        formatted_type = type_mapping.get(fav_type, "👤 User")

        lines = [
            f"⭐ <b>{title}</b>",
            f"{formatted_type}",
            f"🔗 <code>{identifier}</code>"
        ]
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error formatting favorite item: {e}", exc_info=True)
        return "Error displaying favorite item."
        
