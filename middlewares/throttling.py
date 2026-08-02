import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser


class ThrottlingMiddleware(BaseMiddleware):
    """
    Spam & Flood Prevention Throttling Middleware.
    Limits high-frequency user actions to protect bot performance and prevent abuse.
    """

    def __init__(self, rate_limit: float = 0.8):
        self.rate_limit = rate_limit
        self.users_cache: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: TelegramUser = data.get("event_from_user")

        if not event_user:
            return await handler(event, data)

        current_time = time.time()
        user_id = event_user.id

        if user_id in self.users_cache:
            last_time = self.users_cache[user_id]
            if current_time - last_time < self.rate_limit:
                # Rate limit exceeded; silently drop or ignore rapid request
                return None

        self.users_cache[user_id] = current_time
        return await handler(event, data)
      
