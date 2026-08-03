import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, PORT, LOG_LEVEL
from database import Database

# 1. Logging Initialization
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global instances for startup/shutdown management
db = Database()
bot: Bot = None  # type: ignore
dp: Dispatcher = None  # type: ignore


# 5. Router Registration Structure (Future Ready Placeholders / Imports)
# When handler files are created, they should be imported and included in dp.
def register_routers(dispatcher: Dispatcher) -> None:
    """Registers all feature routers into the dispatcher."""
    # Example structure for future routers:
    # from handlers.start import router as start_router
    # from handlers.wallet import router as wallet_router
    # from handlers.marketplace import router as marketplace_router
    # from handlers.profile import router as profile_router
    # from handlers.support import router as support_router
    # from handlers.admin import router as admin_router
    #
    # dispatcher.include_router(start_router)
    # dispatcher.include_router(wallet_router)
    # dispatcher.include_router(marketplace_router)
    # dispatcher.include_router(profile_router)
    # dispatcher.include_router(support_router)
    # dispatcher.include_router(admin_router)
    
    logger.info("Router registration structure initialized (handlers pending implementation).")


# 6. aiohttp Health Server for Render
async def handle_health_check(request: web.Request) -> web.Response:
    """Health check endpoint for Render web service compatibility."""
    return web.Response(text="Bot is running", status=200)


async def start_health_server() -> web.AppRunner:
    """Starts the aiohttp web server on 0.0.0.0 and the specified port."""
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health check server successfully started and listening on 0.0.0.0:{PORT}")
    return runner


# Main Application Lifecycle
async def main() -> None:
    global bot, dp

    logger.info("Initializing Telegram Marketplace Bot...")

    # 2. Bot Initialization
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # 3. Dispatcher Initialization
    dp = Dispatcher()

    # Register Routers
    register_routers(dp)

    # 4. Database Initialization
    try:
        await db.connect()
        await db.init_database()
        logger.info("Database connection established and initialized successfully.")
    except Exception as e:
        logger.critical(f"Critical error during database initialization: {e}")
        sys.exit(1)

    # 6 & 7. Start aiohttp Health Server (Render Compatibility)
    health_runner = None
    try:
        health_runner = await start_health_server()
    except Exception as e:
        logger.critical(f"Failed to start health check server: {e}")
        await db.close()
        sys.exit(1)

    # Start Polling with Proper Error Handling & Graceful Shutdown
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Unhandled exception occurred during bot polling: {e}")
    finally:
        logger.info("Initiating graceful shutdown...")

        # 8. Graceful Shutdown Resources Release
        if health_runner:
            await health_runner.cleanup()
            logger.info("Health check server stopped.")

        if bot and bot.session:
            await bot.session.close()
            logger.info("Bot session closed.")

        if db:
            await db.close()
            logger.info("Database connection closed.")

        logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually via KeyboardInterrupt or SystemExit.")
        
