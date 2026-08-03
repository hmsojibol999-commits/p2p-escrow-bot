import logging
import sys
from telethon import TelegramClient
from config import Config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Initialize Telethon Client using API_ID and API_HASH from config
# 'session' will be the name of the session file generated locally or on Render persistent disk
api_id = Config.API_ID
api_hash = Config.API_HASH

if not api_id or not api_hash:
    logger.error("API_ID or API_HASH is missing in configuration. Telethon client cannot be initialized.")
    sys.exit(1)

# Ensure api_id is integer type as required by Telethon
try:
    parsed_api_id = int(api_id)
except ValueError:
    logger.error("API_ID must be a valid integer.")
    sys.exit(1)

client = TelegramClient("session", parsed_api_id, api_hash)

async def connect_client() -> TelegramClient:
    """
    Connects the Telethon client if it is not already connected.
    Returns the connected TelegramClient instance.
    """
    try:
        if not client.is_connected():
            logger.info("Connecting Telethon client...")
            await client.connect()
            logger.info("Telethon client connected successfully.")
        else:
            logger.debug("Telethon client is already connected.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect Telethon client: {e}", exc_info=True)
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
      
