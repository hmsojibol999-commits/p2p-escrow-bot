import asyncio
import logging
from database.connect import engine
from database.base import BaseModel
# File 026 থেকে সকল মডেল ইমপোর্ট করা হচ্ছে যাতে SQLAlchemy সব টেবিল চিনতে পারে
import database.models  # noqa: F401

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Initializes database tables asynchronously based on registered models.
    Safe to run on startup; existing tables won't be overwritten or dropped.
    """
    try:
        async with engine.begin() as conn:
            logger.info("Initializing database schema and checking tables...")
            await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    # কাজের সুবিধার জন্য ম্যানুয়ালি রান করার অপশন
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
  
