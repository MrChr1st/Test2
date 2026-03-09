import os
import secrets
import string
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg2
from psycopg2.extras import Json, RealDictCursor


def _ensure_sslmode_require(database_url: str) -> str:
    value = (database_url or "").strip()
    if not value:
        return value
    if "sslmode=" in value:
        return value
    parts = urlsplit(value)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["sslmode"] = "require"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class Database:
    def __init__(self, dsn: str):
        self.dsn = _ensure_sslmode_require((dsn or os.getenv("DATABASE_URL", "")).strip())
        if not self.dsn:
            raise ValueError("DATABASE_URL is empty")
        self._init_db()

    def _connect(self):
        return psycopg2.connect(self.dsn, cursor_factory=RealDictCursor, connect_timeout=15, application_name="clientbot")

    def _fetchone(self, sql: str, params=()):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()

    def _fetchall(self, sql: str, params=()):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())

    def _execute(self, sql: str, params=()):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()

    def _init_db(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shared_users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        language TEXT NOT NULL DEFAULT 'ru',
                        ref_code TEXT UNIQUE,
                        referred_by BIGINT,
                        is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shared_exchange_requests (
                        request_id BIGSERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        username TEXT DEFAULT '',
                        profile_link TEXT DEFAULT '',
                        from_currency TEXT NOT NULL,
                        to_currency TEXT NOT NULL,
                        amount_from DOUBLE PRECISION NOT NULL,
                        amount_to DOUBLE PRECISION NOT NULL,
                        receive_details TEXT NOT NULL DEFAULT '',
                        payment_method TEXT NOT NULL DEFAULT '',
                        payment_submethod TEXT NOT NULL DEFAULT '',
                        status TEXT NOT NULL DEFAULT 'waiting_payment',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        paid_at TIMESTAMP NULL,
                        completed_at TIMESTAMP NULL,
                        cancelled_at TIMESTAMP NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shared_exchange_events (
                        id BIGSERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        request_id BIGINT NULL,
                        user_id BIGINT NULL,
                        username TEXT DEFAULT '',
                        profile_link TEXT DEFAULT '',
                        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_users_ref_code ON shared_users(ref_code)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_users_referred_by ON shared_users(referred_by)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_events_created ON shared_exchange_events(created_at DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_events_type_created ON shared_exchange_events(event_type, created_at DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_requests_created ON shared_exchange_requests(created_at DESC)")
            conn.commit()

    def _generate_ref_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(8))
            row = self._fetchone("SELECT 1 FROM shared_users WHERE ref_code = %s", (code,))
            if not row:
                return code

    def _profile_link(self, user_id: int) -> str:
        return f"tg://user?id={user_id}"

    def _log_event(self, event_type: str, request_id: Optional[int], user_id: Optional[int], username: str = "", profile_link: str = "", payload: Optional[dict] = None):
        self._execute(
            """
            INSERT INTO shared_exchange_events (event_type, request_id, user_id, username, profile_link, payload)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (event_type, request_id, user_id, username or "", profile_link or "", Json(payload or {})),
        )

    def create_user_if_not_exists(
        self,
        user_id: int,
        username: Optional[str],
        language: str = "ru",
        referred_by: Optional[int] = None,
    ):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, username, referred_by FROM shared_users WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                if row:
                    cur.execute(
                        """
                        UPDATE shared_users
                        SET username = COALESCE(%s, username),
                            updated_at = NOW()
                        WHERE user_id = %s
                        """,
                        (username, user_id),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO shared_users (user_id, username, language, ref_code, referred_by)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (user_id, username, language, self._generate_ref_code(), referred_by),
                    )
                    cur.execute(
                        """
                        INSERT INTO shared_exchange_events (event_type, user_id, username, profile_link, payload)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            "user_started",
                            user_id,
                            username or "",
                            self._profile_link(user_id),
                            Json({"language": language, "referred_by": referred_by}),
                        ),
                    )
            conn.commit()

    def set_language(self, user_id: int, language: str):
        self._execute(
            "UPDATE shared_users SET language = %s, updated_at = NOW() WHERE user_id = %s",
            (language, user_id),
        )
        user = self._fetchone("SELECT username FROM shared_users WHERE user_id = %s", (user_id,)) or {}
        self._log_event("language_selected", None, user_id, user.get("username", ""), self._profile_link(user_id), {"language": language})

    def get_language(self, user_id: int) -> str:
        row = self._fetchone("SELECT language FROM shared_users WHERE user_id = %s", (user_id,))
        return row["language"] if row else "ru"

    def get_user_ref_code(self, user_id: int) -> Optional[str]:
        row = self._fetchone("SELECT ref_code FROM shared_users WHERE user_id = %s", (user_id,))
        return row["ref_code"] if row else None

    def get_user_id_by_ref_code(self, ref_code: str) -> Optional[int]:
        row = self._fetchone("SELECT user_id FROM shared_users WHERE ref_code = %s", (ref_code,))
        return row["user_id"] if row else None

    def get_referrals_count(self, user_id: int) -> int:
        row = self._fetchone("SELECT COUNT(*) AS c FROM shared_users WHERE referred_by = %s", (user_id,))
        return int(row["c"] or 0) if row else 0

    def count_completed_referral_requests(self, referrer_user_id: int) -> int:
        row = self._fetchone(
            """
            SELECT COUNT(er.request_id) AS c
            FROM shared_exchange_requests er
            JOIN shared_users u ON u.user_id = er.user_id
            WHERE u.referred_by = %s AND er.status = 'done'
            """,
            (referrer_user_id,),
        )
        return int(row["c"] or 0) if row else 0

    def is_user_blocked(self, user_id: int) -> bool:
        row = self._fetchone("SELECT is_blocked FROM shared_users WHERE user_id = %s", (user_id,))
        return bool(row["is_blocked"]) if row else False

    def set_user_blocked(self, user_id: int, blocked: bool):
        self._execute(
            "UPDATE shared_users SET is_blocked = %s, updated_at = NOW() WHERE user_id = %s",
            (blocked, user_id),
        )
        user = self._fetchone("SELECT username FROM shared_users WHERE user_id = %s", (user_id,)) or {}
        self._log_event("user_blocked" if blocked else "user_unblocked", None, user_id, user.get("username", ""), self._profile_link(user_id), {"blocked": blocked})

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
        status: str = "waiting_payment",
    ) -> int:
        profile_link = self._profile_link(user_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO shared_exchange_requests (
                        user_id, username, profile_link, from_currency, to_currency, amount_from, amount_to,
                        receive_details, payment_method, payment_submethod, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING request_id
                    """,
                    (
                        user_id,
                        username or "",
                        profile_link,
                        from_currency,
                        to_currency,
                        float(amount_from),
                        float(amount_to),
                        receive_details,
                        payment_method,
                        payment_submethod,
                        status,
                    ),
                )
                request_id = int(cur.fetchone()["request_id"])
                cur.execute(
                    """
                    INSERT INTO shared_exchange_events (event_type, request_id, user_id, username, profile_link, payload)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        "request_created",
                        request_id,
                        user_id,
                        username or "",
                        profile_link,
                        Json(
                            {
                                "from_currency": from_currency,
                                "to_currency": to_currency,
                                "amount_from": float(amount_from),
                                "amount_to": float(amount_to),
                                "receive_details": receive_details,
                                "payment_method": payment_method,
                                "payment_submethod": payment_submethod,
                                "status": status,
                            }
                        ),
                    ),
                )
            conn.commit()
        return request_id

    def get_active_request(self, user_id: int):
        return self._fetchone(
            """
            SELECT request_id AS id, user_id, username, profile_link, from_currency, to_currency, amount_from,
                   amount_to, receive_details, payment_method, payment_submethod, status,
                   created_at, updated_at, paid_at, completed_at, cancelled_at
            FROM shared_exchange_requests
            WHERE user_id = %s AND status IN ('waiting_payment', 'wallet_operator', 'paid_pending_review')
            ORDER BY request_id DESC LIMIT 1
            """,
            (user_id,),
        )

    def get_request_by_id(self, request_id: int):
        return self._fetchone(
            """
            SELECT request_id AS id, user_id, username, profile_link, from_currency, to_currency, amount_from,
                   amount_to, receive_details, payment_method, payment_submethod, status,
                   created_at, updated_at, paid_at, completed_at, cancelled_at
            FROM shared_exchange_requests WHERE request_id = %s
            """,
            (request_id,),
        )

    def update_request_status(self, request_id: int, status: str):
        row = self.get_request_by_id(request_id)
        if not row:
            return
        paid_at_sql = ", paid_at = NOW()" if status == "paid_pending_review" else ""
        completed_at_sql = ", completed_at = NOW()" if status == "done" else ""
        cancelled_at_sql = ", cancelled_at = NOW()" if status == "cancelled" else ""
        self._execute(
            f"UPDATE shared_exchange_requests SET status = %s, updated_at = NOW(){paid_at_sql}{completed_at_sql}{cancelled_at_sql} WHERE request_id = %s",
            (status, request_id),
        )
        event_type = {
            "paid_pending_review": "paid",
            "done": "request_done",
            "cancelled": "request_cancelled",
        }.get(status, "status_changed")
        self._log_event(
            event_type,
            request_id,
            row["user_id"],
            row.get("username", ""),
            row.get("profile_link", self._profile_link(row["user_id"])),
            {"status": status},
        )

    def get_last_requests(self, limit: int = 100):
        return self._fetchall(
            """
            SELECT request_id AS id, user_id, username, profile_link, from_currency, to_currency, amount_from,
                   amount_to, receive_details, payment_method, payment_submethod, status,
                   created_at, updated_at, paid_at, completed_at, cancelled_at
            FROM shared_exchange_requests
            ORDER BY request_id DESC
            LIMIT %s
            """,
            (limit,),
        )

    def log_opened_exchange(self, user_id: int, username: Optional[str]):
        self._log_event("opened_exchange", None, user_id, username or "", self._profile_link(user_id), {})

    def log_qr_requested(self, request_id: int, user_id: int, username: Optional[str], asset_name: str, target_value: str):
        self._log_event(
            "qr_requested",
            request_id,
            user_id,
            username or "",
            self._profile_link(user_id),
            {"asset_name": asset_name, "target_value": target_value},
        )

    def log_wallet_urgent(self, request_id: int, user_id: int, username: Optional[str], from_currency: str, to_currency: str, amount_from: float, amount_to: float, receive_details: str):
        self._log_event(
            "wallet_urgent",
            request_id,
            user_id,
            username or "",
            self._profile_link(user_id),
            {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount_from": float(amount_from),
                "amount_to": float(amount_to),
                "receive_details": receive_details,
            },
        )
