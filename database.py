import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional


class Database:
    def __init__(self, path: str):
        self.path = path
        self.init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'ru',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    source_currency TEXT NOT NULL,
                    target_currency TEXT NOT NULL,
                    amount REAL NOT NULL,
                    base_rate REAL NOT NULL,
                    final_rate REAL NOT NULL,
                    receive_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_user(self, user_id: int, username: Optional[str], language: str = "ru") -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, language)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
                """,
                (user_id, username, language),
            )

    def set_user_language(self, user_id: int, language: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))

    def get_user_language(self, user_id: int) -> str:
        with self.connect() as conn:
            row = conn.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return row[0] if row else "ru"

    def create_request(
        self,
        user_id: int,
        username: Optional[str],
        source_currency: str,
        target_currency: str,
        amount: float,
        base_rate: float,
        final_rate: float,
        receive_amount: float,
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO requests (
                    user_id,
                    username,
                    source_currency,
                    target_currency,
                    amount,
                    base_rate,
                    final_rate,
                    receive_amount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    source_currency,
                    target_currency,
                    amount,
                    base_rate,
                    final_rate,
                    receive_amount,
                ),
            )
            return int(cursor.lastrowid)

    def update_request_status(self, request_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))

    def get_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
            return dict(row) if row else None

    def list_requests(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM requests WHERE status = ? ORDER BY id DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM requests ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]
