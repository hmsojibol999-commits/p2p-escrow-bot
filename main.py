import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from database.session import init_db, get_session_maker
from middlewares.db import DatabaseMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.logging import RequestLoggingMiddleware
from middlewares.sub_check import ChannelSubscriptionMiddleware

# Import User Routers
from handlers.user.start import router as start_router
from handlers.user.wallet import router as wallet_router
from handlers.user.deposit import router as deposit_router
from handlers.user.withdraw import router as withdraw_router
from handlers.user.transfer import router as transfer_router
from handlers.user.marketplace import router as marketplace_router
from handlers.user.order import router as order_router
from handlers.user.support import router as support_router

# Import Admin Routers
from handlers.admin.dashboard import router as admin_dashboard_router
from handlers.admin.deposits import router as admin_deposits_router
from handlers.admin.withdrawals import router as admin_withdrawals_router
from handlers.admin.disputes import router as admin_disputes_router
from handlers.admin.broadcast import router as admin_broadcast_router


# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("bot.main")


async def main() -> None:
    """
    Main application entry point for initializing database, middlewares, routers, and starting polling.
    """
    logger.info("🚀 Starting Telegram Escrow & Marketplace Bot...")

    # Load configuration
    if not Config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is missing in environment variables!")
        sys.exit(1)

    # Initialize Database
    await init_db()
    session_maker = get_session_maker()

    # Initialize Bot and Dispatcher
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Register Global Middlewares
    dp.update.middleware(RequestLoggingMiddleware())
    dp.update.middleware(ThrottlingMiddleware(rate_limit=0.8))
    dp.update.middleware(ChannelSubscriptionMiddleware())  # Force Join Channel Check Middleware
    dp.update.middleware(DatabaseMiddleware(session_pool=session_maker))

    # Register User Routers
    dp.include_router(start_router)
    dp.include_router(wallet_router)
    dp.include_router(deposit_router)
    dp.include_router(withdraw_router)
    dp.include_router(transfer_router)
    dp.include_router(marketplace_router)
    dp.include_router(order_router)
    dp.include_router(support_router)

    # Register Admin Routers
    dp.include_router(admin_dashboard_router)
    dp.include_router(admin_deposits_router)
    dp.include_router(admin_withdrawals_router)
    dp.include_router(admin_disputes_router)
    dp.include_router(admin_broadcast_router)

    # Drop pending updates and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Bot is online and polling for updates...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("🛑 Bot stopped gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⚠️ Bot interrupted by user.")
