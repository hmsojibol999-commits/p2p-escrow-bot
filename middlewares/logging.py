import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


logger = logging.getLogger("bot.logging")


class RequestLoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging incoming Telegram updates, user interactions, and requests.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        event_type = "UNKNOWN"
        details = ""

        if isinstance(event, Message):
            user = event.from_user
            event_type = "MESSAGE"
            details = event.text or f"[{event.content_type}]"
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            event_type = "CALLBACK"
            details = event.data

        if user:
            username = f"@{user.username}" if user.username else f"ID:{user.id}"
            logger.info(f"[{event_type}] User: {username} ({user.id}) | Action: {details}")

        return await handler(event, data)
      
