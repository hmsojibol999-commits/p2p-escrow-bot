import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    """
    Spam & Flood Prevention Throttling Middleware with user notification.
    Limits high-frequency user actions to protect bot performance and prevent abuse.
    """

    def __init__(self, rate_limit: float = 0.8) -> None:
        super().__init__()
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user ID from Message, CallbackQuery or data context
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
        else:
            event_user = data.get("event_from_user")
            if event_user:
                user_id = event_user.id

        if user_id:
            current_time = time.time()
            last_time = self.user_timestamps.get(user_id, 0.0)

            # Check if user is sending requests too fast
            if current_time - last_time < self.rate_limit:
                # Alert user if it's a callback query to enhance UX
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer("⚠️ Too many requests! Please slow down.", show_alert=True)
                    except Exception:
                        pass
                return None

            # Update timestamp
            self.user_timestamps[user_id] = current_time

        return await handler(event, data)
        
