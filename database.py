import sqlite3
from config import DB_PATH


def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def create_schema(con):
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            full_name TEXT NOT NULL UNIQUE,
            login TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS manufacturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS pickup_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS products (
            article TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            supplier_id INTEGER NOT NULL,
            manufacturer_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            discount INTEGER NOT NULL DEFAULT 0 CHECK(discount >= 0),
            stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
            description TEXT,
            image_path TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            order_date TEXT,
            delivery_date TEXT,
            pickup_point_id INTEGER,
            client_full_name TEXT,
            receive_code INTEGER,
            status TEXT,
            FOREIGN KEY (pickup_point_id) REFERENCES pickup_points(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_article TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_article) REFERENCES products(article)
        );
        """
    )
    con.commit()


def table_empty(con, table):
    return con.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"] == 0


def get_or_create(con, table, name):
    row = con.execute(f"SELECT id FROM {table} WHERE name=?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = con.execute(f"INSERT INTO {table}(name) VALUES(?)", (name,))
    return cur.lastrowid
