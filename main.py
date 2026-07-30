import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# টেলিগ্রাম বট টোকেন
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# /start কমান্ড
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Buy Account (কিনুন)", callback_data="buy")],
        [InlineKeyboardButton(text="📢 Sell Account (বিক্রি করুন)", callback_data="sell")],
        [InlineKeyboardButton(text="💰 Wallet (ওয়ালেট/ব্যালেন্স)", callback_data="wallet")],
        [InlineKeyboardButton(text="👨‍💻 Support (সাহায্য)", callback_data="support")]
    ])
    
    welcome_text = (
        f"👋 **জি {message.from_user.first_name}! P2P Escrow Bot-এ স্বাগতম।**\n\n"
        "এখানে নিরাপদে আইডি কেনাবেচা করতে পারবেন। নিচের যেকোনো অপশনে ক্লিক করুন:"
    )
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query()
async def button_click(callback: types.CallbackQuery):
    data = callback.data
    if data == "buy":
        await callback.message.answer("🛒 **Marketplace:** বর্তমানে বাজারে ১০টি ফেসবুক আইডি এভেলেবেল আছে।")
    elif data == "sell":
        await callback.message.answer("📢 **Sell:** আপনার আইডিগুলো আপলোড করতে তথ্য জমা দিন।")
    elif data == "wallet":
        await callback.message.answer("💰 **Your Wallet:**\n\nবর্তমান ব্যালেন্স: 0.00 BDT")
    elif data == "support":
        await callback.message.answer("👨‍💻 **Support:** কোনো সমস্যা হলে এডমিনকে মেসেজ দিন।")
    
    await callback.answer()

# Render-এর Health Check সফল করার ওয়েব হ্যান্ডলার
async def handle(request):
    return web.Response(text="P2P Escrow Bot is Running Live!")

async def main():
    # Render-এর জন্য ওয়েব সার্ভার চালু করা
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

    # টেলিগ্রাম বট পোলিং
    print("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
