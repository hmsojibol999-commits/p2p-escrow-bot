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



# ==========================
# Logging Setup
# ==========================

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
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



async def main():

    logger.info("Starting Escrow Marketplace Bot...")


    # --------------------------
    # Database Initialize
    # --------------------------

    await init_db()

    session_maker = get_session_maker()


    # --------------------------
    # Bot Initialize
    # --------------------------

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=(
                ParseMode.HTML
                if Config.PARSE_MODE == "HTML"
                else ParseMode.MARKDOWN
            )
        )
    )


    dp = Dispatcher()



    # --------------------------
    # Middleware Register
    # --------------------------

    dp.update.middleware(
        RequestLoggingMiddleware()
    )

    dp.update.middleware(
        ThrottlingMiddleware(
            rate_limit=Config.RATE_LIMIT_MESSAGES_PER_SEC
            if hasattr(Config, "RATE_LIMIT_MESSAGES_PER_SEC")
            else 0.8
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



    # --------------------------
    # Include Routers
    # --------------------------

    user_routers = [
        start_router,
        wallet_router,
        deposit_router,
        withdraw_router,
        transfer_router,
        marketplace_router,
        order_router,
        support_router,
    ]


    admin_routers = [
        admin_dashboard_router,
        admin_deposits_router,
        admin_withdrawals_router,
        admin_disputes_router,
        admin_broadcast_router,
    ]


    for router in user_routers:
        dp.include_router(router)


    for router in admin_routers:
        dp.include_router(router)



    # --------------------------
    # Start Polling
    # --------------------------

    await bot.delete_webhook(
        drop_pending_updates=True
    )


    logger.info(
        "Bot is running successfully..."
    )


    try:

        await dp.start_polling(bot)


    except Exception as e:

        logger.exception(
            f"Bot crashed: {e}"
        )


    finally:

        await bot.session.close()

        logger.info(
            "Bot stopped."
        )



if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logger.info(
            "Shutdown requested."
        )
