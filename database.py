import secrets
import sqlite3
import string
from typing import List, Optional


class Database:
    def __init__(self, path: str):
        self.path = path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'ru',
                    ref_code TEXT UNIQUE,
                    referred_by INTEGER,
                    is_blocked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exchange_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    from_currency TEXT,
                    to_currency TEXT,
                    amount_from REAL,
                    amount_to REAL,
                    receive_details TEXT,
                    payment_method TEXT,
                    payment_submethod TEXT,
                    payment_url TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _generate_ref_code(self, length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_unique_ref_code(self) -> str:
        while True:
            code = self._generate_ref_code()
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM users WHERE ref_code = ?", (code,))
                if not cur.fetchone():
                    return code

    def create_user_if_not_exists(self, user_id: int, username: Optional[str], language: str = "ru", referred_by: Optional[int] = None):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE users SET username = COALESCE(?, username) WHERE user_id = ?", (username, user_id))
                conn.commit()
                return
            ref_code = self._generate_unique_ref_code()
            cur.execute(
                "INSERT INTO users (user_id, username, language, ref_code, referred_by) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, language, ref_code, referred_by),
            )
            conn.commit()

    def set_language(self, user_id: int, language: str):
        with self._connect() as conn:
            conn.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()

    def get_language(self, user_id: int) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return row["language"] if row else "ru"

    def get_user_ref_code(self, user_id: int) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT ref_code FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return row["ref_code"] if row else None

    def get_user_id_by_ref_code(self, ref_code: str) -> Optional[int]:
        with self._connect() as conn:
            row = conn.execute("SELECT user_id FROM users WHERE ref_code = ?", (ref_code,)).fetchone()
            return row["user_id"] if row else None

    def get_referrals_count(self, user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users WHERE referred_by = ?", (user_id,)).fetchone()
            return int(row["c"]) if row else 0

    def count_completed_referral_requests(self, referrer_user_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT COUNT(er.id) AS c
                FROM exchange_requests er
                JOIN users u ON u.user_id = er.user_id
                WHERE u.referred_by = ? AND er.status = 'done'
            """, (referrer_user_id,)).fetchone()
            return int(row["c"]) if row else 0


    def is_user_blocked(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return bool(row["is_blocked"]) if row else False

    def set_user_blocked(self, user_id: int, blocked: bool):
        with self._connect() as conn:
            conn.execute("UPDATE users SET is_blocked = ? WHERE user_id = ?", (1 if blocked else 0, user_id))
            conn.commit()

    def create_exchange_request(
        self,
        user_id: int,
        username: str,
        from_currency: str,
        to_currency: str,
        amount_from: float,
        amount_to: float,
        receive_details: str,
        payment_method: str,
        payment_submethod: str,
        payment_url: str,
        status: str = "waiting_payment",
    ) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO exchange_requests (
                    user_id, username, from_currency, to_currency,
                    amount_from, amount_to, receive_details, payment_method,
                    payment_submethod, payment_url, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, username, from_currency, to_currency,
                amount_from, amount_to, receive_details, payment_method,
                payment_submethod, payment_url, status,
            ))
            conn.commit()
            return cur.lastrowid

    def get_active_request(self, user_id: int):
        with self._connect() as conn:
            return conn.execute("""
                SELECT * FROM exchange_requests
                WHERE user_id = ? AND status IN ('waiting_payment', 'paid_pending_review', 'wallet_operator')
                ORDER BY id DESC LIMIT 1
            """, (user_id,)).fetchone()

    def get_request_by_id(self, request_id: int):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM exchange_requests WHERE id = ?", (request_id,)).fetchone()

    def update_request_status(self, request_id: int, status: str):
        with self._connect() as conn:
            conn.execute("UPDATE exchange_requests SET status = ? WHERE id = ?", (status, request_id))
            conn.commit()

    def get_last_requests(self, limit: int = 100) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("""
                SELECT * FROM exchange_requests
                ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()
