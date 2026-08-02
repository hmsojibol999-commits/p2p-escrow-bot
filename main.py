# ==========================================================
# main.py
#
# Telegram P2P Escrow Marketplace Bot
#
# Compatible:
# Python 3.12
# Aiogram 3.x
# PostgreSQL + SQLAlchemy Async
# ==========================================================

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


from config import Config

from database.session import (
    init_db,
    get_session_maker
)


# Middlewares
from middlewares.db import DatabaseMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.logging import RequestLoggingMiddleware
from middlewares.sub_check import ChannelSubscriptionMiddleware


# User Routers
from handlers.user.start import router as start_router
from handlers.user.wallet import router as wallet_router
from handlers.user.deposit import router as deposit_router
from handlers.user.withdraw import router as withdraw_router
from handlers.user.transfer import router as transfer_router
from handlers.user.marketplace import router as marketplace_router
from handlers.user.order import router as order_router
from handlers.user.support import router as support_router


# Admin Routers
from handlers.admin.dashboard import router as admin_dashboard_router
from handlers.admin.deposits import router as admin_deposits_router
from handlers.admin.withdrawals import router as admin_withdrawals_router
from handlers.admin.disputes import router as admin_disputes_router
from handlers.admin.broadcast import router as admin_broadcast_router



# ==========================================================
# Logging Setup
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("escrow_bot")



# ==========================================================
# Main Function
# ==========================================================

async def main():

    logger.info(
        "🚀 Starting P2P Escrow Marketplace Bot..."
    )


    # ------------------------------
    # Load Config
    # ------------------------------

    if not Config.BOT_TOKEN:
        logger.error(
            "BOT_TOKEN missing!"
        )
        return


    # ------------------------------
    # Database Initialize
    # ------------------------------

    await init_db()

    session_maker = get_session_maker()


    # ------------------------------
    # Telegram Bot Initialize
    # ------------------------------

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )


    dp = Dispatcher()


    # ------------------------------
    # Middleware Register
    # ------------------------------

    dp.update.middleware(
        RequestLoggingMiddleware()
    )

    dp.update.middleware(
        ThrottlingMiddleware(
            rate_limit=Config.RATE_LIMIT_MESSAGES_PER_SEC
        )
    )

    dp.update.middleware(
        ChannelSubscriptionMiddleware()
    )

    dp.update.middleware(
        DatabaseMiddleware(
            session_pool=session_maker
        )
    )


    # ------------------------------
    # User Routers
    # ------------------------------

    dp.include_router(start_router)

    dp.include_router(wallet_router)

    dp.include_router(deposit_router)

    dp.include_router(withdraw_router)

    dp.include_router(transfer_router)

    dp.include_router(marketplace_router)

    dp.include_router(order_router)

    dp.include_router(support_router)



    # ------------------------------
    # Admin Routers
    # ------------------------------

    dp.include_router(
        admin_dashboard_router
    )

    dp.include_router(
        admin_deposits_router
    )

    dp.include_router(
        admin_withdrawals_router
    )

    dp.include_router(
        admin_disputes_router
    )

    dp.include_router(
        admin_broadcast_router
    )


    # ------------------------------
    # Start Bot
    # ------------------------------

    await bot.delete_webhook(
        drop_pending_updates=True
    )


    logger.info(
        "✅ Bot started successfully"
    )


    try:

        await dp.start_polling(
            bot
        )


    except Exception as e:

        logger.exception(
            f"Bot crashed: {e}"
        )


    finally:

        await bot.session.close()

        logger.info(
            "🛑 Bot shutdown complete"
        )



# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped manually"
        )
