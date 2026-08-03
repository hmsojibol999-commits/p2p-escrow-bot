import os
import json
import logging
import re
from typing import List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

FAVORITES_FILE = "favorites.json"

def _ensure_file_exists() -> None:
    """Ensures that the favorites.json file exists. Creates it with an empty list if not."""
    if not os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
            logger.info(f"Created new {FAVORITES_FILE} file.")
        except Exception as e:
            logger.error(f"Failed to create {FAVORITES_FILE}: {e}", exc_info=True)

def _read_favorites() -> List[Dict[str, str]]:
    """Reads and returns all favorites from favorites.json."""
    _ensure_file_exists()
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except json.JSONDecodeError:
        logger.warning(f"{FAVORITES_FILE} was corrupted or empty. Resetting to empty list.")
        return []
    except Exception as e:
        logger.error(f"Error reading {FAVORITES_FILE}: {e}", exc_info=True)
        return []

def _write_favorites(favorites: List[Dict[str, str]]) -> bool:
    """Writes the list of favorites back to favorites.json with pretty formatting."""
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing to {FAVORITES_FILE}: {e}", exc_info=True)
        return False

def _normalize_identifier(identifier: str) -> str:
    """Normalizes username or t.me link to a consistent format (lowercase username or clean link)."""
    identifier = identifier.strip()
    if not identifier:
        return ""
    
    # Check if it's a t.me link or telegram.me link
    tme_match = re.match(r"^(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)", identifier, re.IGNORECASE)
    if tme_match:
        return f"@{tme_match.group(1).lower()}"
    
    # If it starts with @, normalize to lowercase
    if identifier.startswith("@"):
        return identifier.lower()
    
    # If it's a bare username without @
    if re.match(r"^[a-zA-Z0-9_]+$", identifier):
        return f"@{identifier.lower()}"
        
    return identifier.lower()

async def add_favorite(title:
  
