# ==========================================================
# database/session.py
#
# Async SQLAlchemy Database Session Manager
#
# Compatible:
# Python 3.12
# PostgreSQL
# SQLAlchemy 2.x Async
# ==========================================================

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.orm import DeclarativeBase

from config import Config


# ==========================================================
# Database Base Model
# ==========================================================

class Base(DeclarativeBase):
    pass



# ==========================================================
# Database URL Fix
# ==========================================================

def get_database_url() -> str:
    """
    Converts Render PostgreSQL URL format
    to SQLAlchemy async compatible format.
    """

    url = Config.DATABASE_URL

    if url.startswith("postgres://"):
        url = url.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1
        )

    elif url.startswith("postgresql://"):
        url = url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1
        )

    return url



# ==========================================================
# Async Engine
# ==========================================================

engine = create_async_engine(
    get_database_url(),

    echo=Config.DB_ECHO,

    pool_size=Config.DB_POOL_SIZE,

    pool_timeout=Config.DB_POOL_TIMEOUT,

    pool_pre_ping=True,

    future=True,
)



# ==========================================================
# Session Factory
# ==========================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,

    class_=AsyncSession,

    expire_on_commit=False,

)



# ==========================================================
# Initialize Database
# ==========================================================

async def init_db():

    """
    Creates database tables.

    NOTE:
    Production projects should use Alembic migrations.
    This is kept for initial deployment.
    """

    async with engine.begin() as conn:

        await conn.run_sync(
            Base.metadata.create_all
        )



# ==========================================================
# Get Session Maker
# ==========================================================

def get_session_maker():

    return AsyncSessionLocal



# ==========================================================
# Close Database
# ==========================================================

async def close_db():

    await engine.dispose()
