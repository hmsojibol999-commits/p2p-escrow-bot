import os
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

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

def _read_favorites() -> List[Dict[str, Any]]:
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

def _write_favorites(favorites: List[Dict[str, Any]]) -> bool:
    """Writes the list of favorites back to favorites.json with pretty formatting."""
    try:
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing to {FAVORITES_FILE}: {e}", exc_info=True)
        return False

def _normalize_identifier(identifier: str) -> str:
    """Normalizes username or t.me link to a consistent format."""
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

async def add_favorite(title: str, identifier: str, fav_type: str) -> Dict[str, Any]:
    """
    Adds a new favorite entity with title, identifier, type, and created time.
    Validates identifier, checks for duplicates, and saves to favorites.json.
    """
    title = title.strip()
    identifier = identifier.strip()
    fav_type = fav_type.strip().lower()

    if not title:
        return {"success": False, "message": "Title cannot be empty."}
    
    if not identifier:
        return {"success": False, "message": "Username or link cannot be empty."}

    valid_types = {"user", "group", "channel", "bot"}
    if fav_type not in valid_types:
        return {"success": False, "message": f"Invalid type. Must be one of: {', '.join(valid_types)}"}

    # Validate and normalize identifier
    normalized_id = _normalize_identifier(identifier)
    if not normalized_id or (not normalized_id.startswith("@") and not normalized_id.startswith("http")):
        return {"success": False, "message": "Invalid username or Telegram link format."}

    favorites = _read_favorites()

    # Check for duplicate entry (by normalized identifier or exact title)
    for fav in favorites:
        if fav.get("identifier") == normalized_id:
            return {"success": False, "message": f"Favorite with identifier '{identifier}' already exists."}
        if fav.get("title", "").lower() == title.lower():
            return {"success": False, "message": f"Favorite with title '{title}' already exists."}

    created_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    new_entry = {
        "title": title,
        "identifier": normalized_id,
        "type": fav_type,
        "created_time": created_time
    }

    favorites.append(new_entry)
    if _write_favorites(favorites):
        logger.info(f"Added new favorite: {title} ({normalized_id}) [{fav_type}]")
        return {"success": True, "message": f"Successfully added '{title}' to favorites!"}
    
    return {"success": False, "message": "Failed to save favorite due to internal storage error."}

async def get_favorites() -> List[Dict[str, Any]]:
    """Retrieves all saved favorites."""
    return _read_favorites()

async def search_favorites(keyword: str) -> List[Dict[str, Any]]:
    """
    Searches favorites by matching a keyword against title, identifier, or type.
    """
    keyword = keyword.strip().lower()
    if not keyword:
        return await get_favorites()

    favorites = _read_favorites()
    results = []

    for fav in favorites:
        if (keyword in fav.get("title", "").lower() or
            keyword in fav.get("identifier", "").lower() or
            keyword in fav.get("type", "").lower()):
            results.append(fav)

    return results

async def delete_favorite(key: str) -> Dict[str, Any]:
    """
    Deletes a favorite by matching either its title or identifier (username/link).
    """
    key = key.strip()
    if not key:
        return {"success": False, "message": "Search key for deletion cannot be empty."}

    favorites = _read_favorites()
    normalized_key = _normalize_identifier(key)
    
    initial_count = len(favorites)
    updated_favorites = []
    deleted_item = None
    
    for fav in favorites:
        fav_title = fav.get("title", "").lower()
        fav_id = fav.get("identifier", "").lower()
        
        if fav_title == key.lower() or fav_id == normalized_key or fav_id == key.lower():
            deleted_item = fav
        else:
            updated_favorites.append(fav)

    if len(updated_favorites) == initial_count:
        return {"success": False, "message": f"No favorite found matching '{key}'."}

    if _write_favorites(updated_favorites):
        logger.info(f"Deleted favorite: {deleted_item.get('title')} ({deleted_item.get('identifier')})")
        return {"success": True, "message": f"Successfully deleted '{deleted_item.get('title')}' from favorites."}

    return {"success": False, "message": "Failed to update storage during deletion."}
                               
