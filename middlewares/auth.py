from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from database.connect import async_session_factory
from database.models.user import User, UserRole
from services.wallet_service import WalletService


class AuthMiddleware(BaseMiddleware):
    """
    Authentication and Automatic User Onboarding Middleware.
    Ensures user records exist in DB, creates default wallets,
    and blocks banned or suspended users from taking actions.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: TelegramUser = data.get("event_from_user")

        if not event_user or event_user.is_bot:
            return await handler(event, data)

        async with async_session_factory() as session:
            # Check or create user record
            user = await User.get_by_telegram_id(session, event_user.id)

            if not user:
                user = User(
                    telegram_id=event_user.id,
                    username=event_user.username,
                    first_name=event_user.first_name,
                    last_name=event_user.last_name,
                    role=UserRole.BUYER,
                )
                session.add(user)
                await session.flush()

                # Automatically instantiate user wallet
                await WalletService.get_or_create_wallet(session, user.id)
                await session.commit()
            else:
                # Synchronize updated username/profile info
                updated = False
                if user.username != event_user.username:
                    user.username = event_user.username
                    updated = True
                if user.first_name != event_user.first_name:
                    user.first_name = event_user.first_name
                    updated = True
                
                if updated:
                    await session.commit()

            # Enforce Block/Ban restriction
            if user.is_blocked or user.is_banned:
                return None  # Drop execution silently or reject restricted user

            # Attach user DB entity to handler context data
            data["db_user"] = user
            data["db_session"] = session

            return await handler(event, data)
          
