
import os
import sqlite3

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "examguard.db")


def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    return connection


def init_db():
    connection = get_db()
    connection.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

