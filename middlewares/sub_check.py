from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config


class ChannelSubscriptionMiddleware(BaseMiddleware):
    """
    Middleware to force users to join specified Telegram channels before using the bot.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user from event
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        # Ignore if no user or user is a bot
        if not user or user.is_bot:
            return await handler(event, data)

        bot = data["bot"]
        
        # Get channels from Config
        channels = [getattr(Config, "CHANNEL_1", None), getattr(Config, "CHANNEL_2", None)]
        channels = [c for c in channels if c] # Filter out None/empty values

        if not channels:
            return await handler(event, data)

        # Check membership for each channel
        not_joined_channels = []
        for channel in channels:
            try:
                member = await bot.get_chat_member(chat_id=channel, user_id=user.id)
                if member.status in ["left", "kicked"]:
                    not_joined_channels.append(channel)
            except Exception:
                pass

        # If user has not joined all required channels
        if not_joined_channels:
            buttons = []
            for idx, ch in enumerate(channels, 1):
                ch_clean = ch.lstrip("@")
                buttons.append([InlineKeyboardButton(text=f"📢 Join Channel {idx}", url=f"https://t.me/{ch_clean}")])
            
            buttons.append([InlineKeyboardButton(text="🔄 I Have Joined (Check)", callback_data="check_subscription")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            warning_text = (
                "⚠️ **Access Denied!**\n\n"
                "To use this bot, you must join our official channels first.\n"
                "Please join the channels below and click the **'I Have Joined'** button."
            )

            if isinstance(event, Message):
                await event.answer(warning_text, reply_markup=keyboard)
                return
            elif isinstance(event, CallbackQuery):
                if event.data == "check_subscription":
                    await event.answer("❌ You still haven't joined all channels!", show_alert=True)
                else:
                    await event.message.answer(warning_text, reply_markup=keyboard)
                return

        return await handler(event, data)
      
