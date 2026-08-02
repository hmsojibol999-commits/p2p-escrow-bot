from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.models.user import User


class DatabaseMiddleware(BaseMiddleware):
    """
    Unified Database Session and User Injection Middleware.
    Manages the lifecycle of an async SQLAlchemy session, handles commit/rollback safely,
    and automatically fetches or registers the Telegram user for every incoming update.
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Determine Telegram user from event (Message or CallbackQuery)
        telegram_user = None
        if isinstance(event, Message):
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user

        async with self.session_pool() as session:
            # Inject session into handler data
            data["db_session"] = session

            try:
                # Fetch or register user if applicable
                if telegram_user and not telegram_user.is_bot:
                    db_user = await User.get_by_telegram_id(session, telegram_user.id)
                    if not db_user:
                        # Auto-register user if missing
                        db_user = User(
                            telegram_id=telegram_user.id,
                            username=telegram_user.username,
                            first_name=telegram_user.first_name,
                            last_name=telegram_user.last_name,
                        )
                        session.add(db_user)
                        await session.commit()
                        await session.refresh(db_user)
                    
                    # Inject db_user instance into handler data
                    data["db_user"] = db_user

                # Execute handler and commit changes if successful
                result = await handler(event, data)
                await session.commit()
                return result

            except Exception:
                await session.rollback()
                raise
                
