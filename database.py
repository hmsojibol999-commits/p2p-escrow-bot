import os
import logging
import aiosqlite
from typing import Any, List, Optional, Tuple, Union
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = DATABASE_PATH) -> None:
        self.db_path: str = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        self._in_transaction: bool = False

    async def connect(self) -> None:
        """Establishes a shared async connection to SQLite database, ensuring directories exist and applying PRAGMA settings."""
        if self.connection is not None:
            return

        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

        try:
            self.connection = await aiosqlite.connect(self.db_path)
            self.connection.row_factory = aiosqlite.Row

            # Apply PRAGMA optimizations and constraints
            await self.connection.execute("PRAGMA foreign_keys = ON;")
            await self.connection.execute("PRAGMA journal_mode = WAL;")
            await self.connection.execute("PRAGMA synchronous = NORMAL;")
            await self.connection.execute("PRAGMA temp_store = MEMORY;")
            await self.connection.commit()
            
            logger.info(f"Successfully connected to database at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database at {self.db_path}: {e}")
            raise

    async def close(self) -> None:
        """Closes the shared database connection if it is open."""
        if self.connection is not None:
            try:
                await self.connection.close()
                self.connection = None
                logger.info("Database connection closed successfully.")
            except Exception as e:
                logger.error(f"Error while closing database connection: {e}")
                raise

    async def init_database(self) -> None:
        """Initializes the database by creating all necessary tables and indexes."""
        await self.create_tables()
        await self.create_indexes()
        logger.info("Database initialized successfully with tables and indexes.")

    async def create_tables(self) -> None:
        """Creates all required database tables with constraints and foreign keys."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")

        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                join_date TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                is_banned INTEGER NOT NULL DEFAULT 0 CHECK (is_banned IN (0, 1)),
                total_orders INTEGER NOT NULL DEFAULT 0
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS wallets (
                telegram_id INTEGER PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 0.0 CHECK (balance >= 0.0),
                total_deposit REAL NOT NULL DEFAULT 0.0 CHECK (total_deposit >= 0.0),
                total_withdraw REAL NOT NULL DEFAULT 0.0 CHECK (total_withdraw >= 0.0),
                total_spent REAL NOT NULL DEFAULT 0.0 CHECK (total_spent >= 0.0),
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                number TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
                display_order INTEGER NOT NULL DEFAULT 0
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS deposit_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                payment_method TEXT NOT NULL,
                payment_number TEXT NOT NULL,
                sender_number TEXT NOT NULL,
                transaction_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed', 'cancelled')),
                created_at TEXT NOT NULL,
                approved_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                payment_method TEXT NOT NULL,
                receive_number TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed', 'cancelled')),
                created_at TEXT NOT NULL,
                approved_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL CHECK (price >= 0),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending', 'approved', 'rejected', 'completed', 'cancelled')),
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS product_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                sold INTEGER NOT NULL DEFAULT 0 CHECK (sold IN (0, 1)),
                sold_at TEXT,
                order_id INTEGER,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                item_content TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'approved', 'rejected', 'completed', 'cancelled')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            );
            """
        ]

        try:
            async with self.connection:
                for sql in tables_sql:
                    await self.connection.execute(sql)
                await self.connection.commit()
            logger.info("All database tables created successfully.")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    async def create_indexes(self) -> None:
        """Creates indexes for optimized database querying."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")

        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_wallets_telegram_id ON wallets(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_deposit_requests_status ON deposit_requests(status);",
            "CREATE INDEX IF NOT EXISTS idx_deposit_requests_telegram_id ON deposit_requests(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_withdraw_requests_status ON withdraw_requests(status);",
            "CREATE INDEX IF NOT EXISTS idx_withdraw_requests_telegram_id ON withdraw_requests(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_categories_id ON categories(id);",
            "CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);",
            "CREATE INDEX IF NOT EXISTS idx_products_id ON products(id);",
            "CREATE INDEX IF NOT EXISTS idx_product_items_product_id ON product_items(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_items_sold ON product_items(sold);",
            "CREATE INDEX IF NOT EXISTS idx_orders_telegram_id ON orders(telegram_id);",
            "CREATE INDEX IF NOT EXISTS idx_orders_id ON orders(id);",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
            "CREATE INDEX IF NOT EXISTS idx_transactions_telegram_id ON transactions(telegram_id);"
        ]

        try:
            async with self.connection:
                for sql in indexes_sql:
                    await self.connection.execute(sql)
                await self.connection.commit()
            logger.info("All database indexes created successfully.")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    async def execute(self, query: str, parameters: Tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        """Executes a single SQL query with optional parameters."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            cursor = await self.connection.execute(query, parameters)
            if not self._in_transaction:
                await self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"Query execution failed: {query} with params {parameters}. Error: {e}")
            raise

    async def executemany(self, query: str, parameters: List[Tuple[Any, ...]]) -> aiosqlite.Cursor:
        """Executes a batch SQL query with a sequence of parameters."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            cursor = await self.connection.executemany(query, parameters)
            if not self._in_transaction:
                await self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"Batch execution failed: {query}. Error: {e}")
            raise

    async def fetchone(self, query: str, parameters: Tuple[Any, ...] = ()) -> Optional[aiosqlite.Row]:
        """Executes a query and fetches a single row result."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            async with self.connection.execute(query, parameters) as cursor:
                row = await cursor.fetchone()
                return row
        except Exception as e:
            logger.error(f"Fetchone failed: {query} with params {parameters}. Error: {e}")
            raise

    async def fetchall(self, query: str, parameters: Tuple[Any, ...] = ()) -> List[aiosqlite.Row]:
        """Executes a query and fetches all row results."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            async with self.connection.execute(query, parameters) as cursor:
                rows = await cursor.fetchall()
                return rows
        except Exception as e:
            logger.error(f"Fetchall failed: {query} with params {parameters}. Error: {e}")
            raise

    async def begin(self) -> None:
        """Begins an explicit database transaction."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            await self.connection.execute("BEGIN TRANSACTION;")
            self._in_transaction = True
        except Exception as e:
            logger.error(f"Failed to begin transaction: {e}")
            raise

    async def commit(self) -> None:
        """Commits the current active transaction."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            await self.connection.commit()
            self._in_transaction = False
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise

    async def rollback(self) -> None:
        """Rolls back the current active transaction."""
        if self.connection is None:
            raise RuntimeError("Database connection is not established. Call connect() first.")
        try:
            await self.connection.rollback()
            self._in_transaction = False
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise
            
