import logging
import sys
from telethon import TelegramClient
from config import Config

logger = logging.getLogger(__name__)

api_id = Config.API_ID
api_hash = Config.API_HASH
bot_token = Config.BOT_TOKEN

if not api_id or not api_hash or not bot_token:
    logger.error("API_ID, API_HASH, or BOT_TOKEN is missing in configuration.")
    sys.exit(1)

try:
    parsed_api_id = int(api_id)
except ValueError:
    logger.error("API_ID must be a valid integer.")
    sys.exit(1)

# Initialize Telethon Client as a Bot (passing bot_token prevents interactive prompt)
client = TelegramClient("session", parsed_api_id, api_hash)

async def connect_client() -> TelegramClient:
    """
    Connects the Telethon client and starts with bot token if not authorized.
    """
    try:
        if not client.is_connected():
            logger.info("Connecting Telethon client...")
            await client.connect()
            
            # If not already authorized as a bot, sign in using the BOT_TOKEN
            if not await client.is_user_authorized():
                logger.info("Signing in Telethon client using bot token...")
                await client.sign_in(bot=bot_token)
                
            logger.info("Telethon client connected and authorized successfully.")
        else:
            logger.debug("Telethon client is already connected.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect/authorize Telethon client: {e}", exc_info=True)
        raise

async def disconnect_client() -> None:
    """
    Disconnects the Telethon client safely if it is currently connected.
    """
    try:
        if client.is_connected():
            logger.info("Disconnecting Telethon client...")
            await client.disconnect()
            logger.info("Telethon client disconnected successfully.")
        else:
            logger.debug("Telethon client was already disconnected.")
    except Exception as e:
        logger.error(f"Error occurred while disconnecting Telethon client: {e}", exc_info=True)
        raise
        
