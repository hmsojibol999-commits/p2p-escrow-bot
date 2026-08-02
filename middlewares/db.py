from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.connect import async_session_factory


class DatabaseSessionMiddleware(BaseMiddleware):
    """
    Database Session Injection and Lifecycle Middleware.
    Manages the lifecycle of an async SQLAlchemy session for every incoming Telegram update,
    ensuring proper cleanup, commit, or rollback.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Check if auth middleware already provided a session
        if "db_session" in data:
            return await handler(event, data)

        async with async_session_factory() as session:
            data["db_session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
              
