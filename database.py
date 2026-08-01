import sqlite3

DB_NAME = "marketplace.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table (Role, Balance, Trust Score, Language)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        balance REAL DEFAULT 0.0,
        role TEXT DEFAULT 'buyer', -- 'buyer', 'seller', 'admin'
        trust_score INTEGER DEFAULT 100,
        language TEXT DEFAULT 'bn',
        status TEXT DEFAULT 'active', -- 'active', 'banned'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Main Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'active'
    )
    """)

    # 3. Products / Stock Table (Requires Admin Approval)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id INTEGER,
        category_id INTEGER,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        credentials_data TEXT NOT NULL, -- Stock credentials (e.g. email:pass)
        stock_count INTEGER DEFAULT 0,
        rating REAL DEFAULT 5.0,
        status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'out_of_stock'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (seller_id) REFERENCES users(user_id),
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)

    # 4. Orders & Escrow Ledger Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id TEXT UNIQUE NOT NULL,
        buyer_id INTEGER,
        seller_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        total_price REAL,
        platform_fee REAL DEFAULT 0.0,
        escrow_status TEXT DEFAULT 'held', -- 'held', 'released', 'disputed', 'refunded'
        delivered_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES users(user_id),
        FOREIGN KEY (seller_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    # 5. Transactions Ledger (Deposits & Withdrawals)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT, -- 'deposit', 'withdraw'
        method TEXT, -- 'bkash', 'nagad', 'rocket', 'binance'
        amount REAL,
        charge REAL DEFAULT 0.0,
        account_info TEXT,
        status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Disputes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disputes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        buyer_id INTEGER,
        reason TEXT,
        proof_text TEXT,
        status TEXT DEFAULT 'open', -- 'open', 'resolved_buyer', 'resolved_seller'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("✅ P2P Escrow Database Initialized Successfully!")

if __name__ == "__main__":
    init_db()
    
