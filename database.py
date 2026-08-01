import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "bot_database.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. USERS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.0,
            role TEXT DEFAULT 'buyer',
            status TEXT DEFAULT 'active',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. DYNAMIC CATEGORIES TABLE (Admin Managed)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # 3. DYNAMIC CUSTOM FIELDS / FILTERS TABLE (Admin Managed)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            filter_name TEXT NOT NULL,
            filter_type TEXT DEFAULT 'text', -- text, number, select
            options TEXT, -- JSON string for dropdown options
            is_required INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')

    # 4. SELLER SHOPS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER UNIQUE,
            shop_name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, suspended
            rating REAL DEFAULT 5.0,
            total_sales INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users (user_id)
        )
    ''')

    # 5. DYNAMIC PRODUCTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER,
            category_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            total_stock INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active', -- active, inactive, out_of_stock
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')

    # 6. DYNAMIC PRODUCT ATTRIBUTES / FILTER VALUES TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_attributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            filter_id INTEGER,
            attribute_value TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (filter_id) REFERENCES category_filters (id)
        )
    ''')

    # 7. DIGITAL INVENTORY / STOCK LOCKER TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            item_data TEXT NOT NULL, -- Account credentials / Cookies / Digital Data
            is_sold INTEGER DEFAULT 0,
            sold_to_user_id INTEGER,
            sold_at TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 8. ESCROW TRANSACTIONS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escrow_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            seller_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            commission_amount REAL NOT NULL,
            status TEXT DEFAULT 'holding', -- holding, completed, disputed, refunded, partial_refunded
            timer_minutes INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users (user_id),
            FOREIGN KEY (seller_id) REFERENCES users (user_id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # 9. DISPUTES & EVIDENCE TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disputes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escrow_id INTEGER UNIQUE,
            opened_by INTEGER,
            reason TEXT NOT NULL,
            evidence_data TEXT,
            status TEXT DEFAULT 'open', -- open, resolved_buyer, resolved_seller, partial_resolved
            admin_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (escrow_id) REFERENCES escrow_trades (id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Dynamic Database Models Initialized Successfully!")
  
