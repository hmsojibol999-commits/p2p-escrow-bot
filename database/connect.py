import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

# File 001 (config.py) থেকে কনফিগারেশন ইমপোর্ট
from config import config

logger = logging.getLogger("DatabaseEngine")

# Global Engine & Session Factory References
engine: Optional[AsyncEngine] = None
AsyncSessionFactory: Optional[async_sessionmaker[AsyncSession]] = None


def get_async_database_url(url: str) -> str:
    """
    Ensure the Database URL uses asyncpg driver for async operations.
    Converts postgresql:// or postgres:// to postgresql+asyncpg://
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def init_database() -> bool:
    """
    Initializes the Async SQLAlchemy Engine and tests the database connection.
    Called during application startup (main.py).
    """
    global engine, AsyncSessionFactory

    try:
        db_url = get_async_database_url(config.DATABASE_URL)

        # Create Async Engine with production pool options from config.py
        engine = create_async_engine(
            db_url,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=10,
            pool_timeout=config.DB_POOL_TIMEOUT,
            pool_pre_ping=config.DB_AUTO_RECONNECT,
            echo=config.DB_ECHO,
        )

        # Create Session Factory
        AsyncSessionFactory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Verify connection
        connection_status = await check_database_connection()
        if connection_status:
            logger.info("PostgreSQL Database Engine initialized successfully.")
            return True
        else:
            logger.critical("Database initialization failed during connection check.")
            return False

    except SQLAlchemyError as e:
        logger.critical(f"Database Initialization Error: {type(e).__name__}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error during database initialization: {type(e).__name__}")
        return False


async def check_database_connection() -> bool:
    """
    Health check function to test if the database is alive and reachable.
    Executes a simple SELECT 1 query via AsyncEngine.
    """
    global engine
    if not engine:
        logger.error("Health Check Failed: Database Engine is not initialized.")
        return False

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("Database Health Check passed.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database Connection Health Check Failed: {type(e).__name__}")
        return False
    except Exception as e:
        logger.error(f"Database Health Check Exception: {type(e).__name__}")
        return False


async def close_database() -> None:
    """
    Closes database connection pools gracefully during shutdown.
    Called during application cleanup.
    """
    global engine
    if engine:
        logger.info("Closing database engine pool connections...")
        await engine.dispose()
        logger.info("Database engine connections disposed successfully.")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Helper to get the global session factory for database operations.
    """
    if AsyncSessionFactory is None:
        raise RuntimeError("Database session factory is not initialized. Call init_database() first.")
    return AsyncSessionFactory
