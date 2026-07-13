import sqlite3
import os
import time
from threading import Lock

DB_PATH = os.getenv("MEMORY_DB", "memory.db")
_lock = Lock()


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts REAL NOT NULL
        )"""
    )
    con.commit()
    con.close()


def add_message(session_id, role, content):
    with _lock:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO messages (session_id, role, content, ts) VALUES (?,?,?,?)",
            (session_id, role, content, time.time()),
        )
        con.commit()
        con.close()


def get_history(session_id, limit=8):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    con.close()
    # reverse so the oldest comes first
    history = [{"role": r, "content": c} for r, c in rows][::-1]
    return history
