import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)

# Ruta exacta: E:\catalia-bolivia\backend\database\catalia_local.db
DB_NAME = os.path.join(DB_DIR, "catalia_local.db")


def get_connection(row_factory: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute("PRAGMA foreign_keys = ON;")
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cursor: sqlite3.Cursor, table: str, column: str, definition: str) -> None:
    cursor.execute(f"PRAGMA table_info({table})")
    existing_cols = {col[1] for col in cursor.fetchall()}
    if column not in existing_cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    print(f"[DB] Conectando a: {os.path.abspath(DB_NAME)}")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            whatsapp TEXT DEFAULT '',
            plan_type TEXT DEFAULT 'free',
            flyers_generated INTEGER DEFAULT 0
        )
    """)

    _ensure_column(cursor, "users", "whatsapp", "TEXT DEFAULT ''")
    _ensure_column(cursor, "users", "plan_type", "TEXT DEFAULT 'free'")
    _ensure_column(cursor, "users", "flyers_generated", "INTEGER DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            price REAL,
            currency TEXT DEFAULT 'Bs',
            category TEXT,
            commercial_description TEXT,
            urgency_phrase TEXT,
            estrategia_promocion TEXT,
            color_sugerido_fondo TEXT,
            color_sugerido_acento TEXT,
            image_data TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    _ensure_column(cursor, "products", "currency", "TEXT DEFAULT 'Bs'")
    _ensure_column(cursor, "products", "estrategia_promocion", "TEXT")
    _ensure_column(cursor, "products", "color_sugerido_fondo", "TEXT")
    _ensure_column(cursor, "products", "color_sugerido_acento", "TEXT")
    _ensure_column(cursor, "products", "image_data", "TEXT")

    conn.commit()

    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@catalia.bo",))
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO users (business_name, email, password, whatsapp, plan_type, flyers_generated)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Administración CataliA",
                "admin@catalia.bo",
                "admin123",
                "",
                "campana",
                0,
            ),
        )
        conn.commit()

    conn.close()