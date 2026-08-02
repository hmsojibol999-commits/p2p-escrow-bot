import logging

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from config import Config


logger = logging.getLogger("database.session")


# ==========================
# Database Engine
# ==========================

DATABASE_URL = Config.DATABASE_URL


# Fix PostgreSQL async driver compatibility
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1
    )


engine = create_async_engine(
    DATABASE_URL,
    echo=Config.DB_ECHO,
    pool_size=Config.DB_POOL_SIZE,
    pool_timeout=Config.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
)


# ==========================
# Session Factory
# ==========================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_session_maker():
    """
    Returns async database session factory.
    """
    return AsyncSessionLocal



# ==========================
# Database Initialize
# ==========================

async def init_db():

    from database.models.base import Base


    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )


    logger.info(
        "Database initialized successfully."
    )



# ==========================
# Database Shutdown
# ==========================

async def close_db():

    await engine.dispose()

    logger.info(
        "Database connection closed."
    )
