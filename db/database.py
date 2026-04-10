import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join("data", "regulaintel.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Chat Sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chat Messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            circular_refs TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
    """)

    # Circular Versioning
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS circular_versions (
            circular_id TEXT,
            source TEXT,
            version_number INTEGER,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            chunk_ids TEXT,
            PRIMARY KEY (circular_id, version_number)
        )
    """)

    conn.commit()
    conn.close()

# Initialize immediately on module import
init_db()
