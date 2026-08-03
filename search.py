import logging
import asyncio
from typing import List, Dict, Any, Optional
from telethon import errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel, Chat, User
from telethon_client import connect_client, disconnect_client

# Configure logging
logger = logging.getLogger(__name__)

async def search_telegram(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Searches public Telegram users, groups, and channels using Telethon.
    
    Args:
        query (str): The search keyword.
        limit (int): Maximum number of results to return (default: 10, max: 10).
        
    Returns:
        dict: {'success': bool, 'message': str, 'results': list}
    """
    query = query.strip()
    if not query:
        return {
            "success": False,
            "message": "Search keyword cannot be empty.",
            "results": []
        }

    # Ensure limit doesn't exceed reasonable bounds
    limit = max(1, min(limit, 10))

    client = None
    try:
        # Connect to Telethon client
        client = await connect_client()

        logger.info(f"Performing public Telegram search for query: '{query}' (limit: {limit})")

        # Use contacts.SearchRequest for public global search
        result = await client(SearchRequest(
            q=query,
            limit=limit
        ))

        formatted_results = []

        # Combine users, chats (groups/channels) from the search result
        all_chats = list(result.chats) if hasattr(result, 'chats') else []
        all_users = list(result.users) if hasattr(result, 'users') else []

        combined_entities = all_chats + all_users

        for entity in combined_entities[:limit]:
            entity_id = getattr(entity, 'id', None)
            title = ""
            username = getattr(entity, 'username', None)
            entity_type = "unknown"
            tme_link = ""

            if isinstance(entity, User):
                if entity.bot:
                    entity_type = "bot"
                else:
                    entity_type = "user"
                
                first_name = entity.first_name or ""
                last_name = entity.last_name or ""
                title = f"{first_name} {last_name}".strip()
                if not title and username:
                    title = f"@{username}"

            elif isinstance(entity, Chat):
                entity_type = "group"
                title = getattr(entity, 'title', 'Untitled Group')

            elif isinstance(entity, Channel):
                if getattr(entity, 'megagroup', False):
                    entity_type = "group"
                else:
                    entity_type = "channel"
                title = getattr(entity, 'title', 'Untitled Channel')

            # Build t.me link if username exists
            if username:
                tme_link = f"https://t.me/{username}"

            formatted_results.append({
                "id": entity_id,
                "title": title or "N/A",
                "username": f"@{username}" if username else None,
                "type": entity_type,
                "tme_link": tme_link if tme_link else None
            })

        return {
            "success": True,
            "message": f"Found {len(formatted_results)} result(s) for '{query}'.",
            "results": formatted_results
        }

    except errors.FloodWaitError as e:
        logger.warning(f"FloodWait encountered during search: must wait {e.seconds} seconds.")
        return {
            "success": False,
            "message": f"Telegram rate limit hit (FloodWait). Please try again after {e.seconds} seconds.",
            "results": []
        }
    except errors.TimeoutError:
        logger.error("Search request timed out.")
        return {
            "success": False,
            "message": "The search request timed out. Please try again later.",
            "results": []
        }
    except (errors.RPCError, ConnectionError) as e:
        logger.error(f"Telegram connection/RPC error during search: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Connection error with Telegram network: {str(e)}",
            "results": []
        }
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}",
            "results": []
        }
      
