import sqlite3
from contextlib import closing
from typing import Any, Dict, List, Optional


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    language TEXT NOT NULL DEFAULT 'ru',
                    referrer_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exchange_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    from_currency TEXT NOT NULL,
                    to_currency TEXT NOT NULL,
                    amount REAL NOT NULL,
                    result_amount REAL NOT NULL,
                    from_rate_usd REAL NOT NULL,
                    to_rate_usd REAL NOT NULL,
                    client_bonus REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def upsert_user(self, user_id: int, username: Optional[str], full_name: str, language: str = "ru", referrer_id: Optional[int] = None) -> None:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id, referrer_id FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "INSERT INTO users (user_id, username, full_name, language, referrer_id) VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, full_name, language, referrer_id),
                )
            else:
                final_ref = row["referrer_id"] if row["referrer_id"] is not None else referrer_id
                cur.execute(
                    "UPDATE users SET username = ?, full_name = ?, language = ?, referrer_id = ? WHERE user_id = ?",
                    (username, full_name, language, final_ref, user_id),
                )
            conn.commit()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def set_language(self, user_id: int, language: str) -> None:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()

    def create_exchange_request(self, user_id: int, username: Optional[str], full_name: str, from_currency: str, to_currency: str, amount: float, result_amount: float, from_rate_usd: float, to_rate_usd: float, client_bonus: float) -> int:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO exchange_requests (
                    user_id, username, full_name, from_currency, to_currency,
                    amount, result_amount, from_rate_usd, to_rate_usd, client_bonus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, from_currency, to_currency, amount, result_amount, from_rate_usd, to_rate_usd, client_bonus))
            conn.commit()
            return int(cur.lastrowid)

    def get_referral_count(self, user_id: int) -> int:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE referrer_id = ?", (user_id,))
            return int(cur.fetchone()["cnt"])

    def get_total_users(self) -> int:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            return int(cur.fetchone()["cnt"])

    def get_total_requests(self) -> int:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM exchange_requests")
            return int(cur.fetchone()["cnt"])

    def get_requests_today(self) -> int:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM exchange_requests WHERE DATE(created_at) = DATE('now')")
            return int(cur.fetchone()["cnt"])

    def get_last_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM exchange_requests ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]
