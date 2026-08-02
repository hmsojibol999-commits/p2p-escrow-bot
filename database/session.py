import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# File 003 (database/connect.py) থেকে Session Factory ইমপোর্ট
from database.connect import get_session_factory

logger = logging.getLogger("DatabaseSession")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator function that yields an AsyncSession.
    Provides automatic commit on success, automatic rollback on error,
    and ensures session closure after operation completion.
    
    Usage Pattern:
        async for session in get_session():
            # Perform DB Operations
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database Session Transaction Error: {type(e).__name__}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error during session lifecycle: {type(e).__name__}")
            raise
        finally:
            await session.close()


async def get_direct_session() -> AsyncSession:
    """
    Helper to return a raw AsyncSession instance.
    Caller must manually handle commit, rollback, and session.close().
    """
    session_factory = get_session_factory()
    return session_factory()
  
