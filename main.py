import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, PORT
from database import db
from handlers import start, wallet, marketplace, profile, support, admin

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="Bot is running smoothly!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health server started on port {PORT}")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register Routers
    dp.include_router(start.router)
    dp.include_router(wallet.router)
    dp.include_router(marketplace.router)
    dp.include_router(profile.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)

    # Start aiohttp health server for Render
    await start_web_server()

    logger.info("Starting Telegram Bot Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
      
