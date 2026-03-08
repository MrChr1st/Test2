import asyncio
import os

import psycopg2
from psycopg2.extras import Json, RealDictCursor


_inited = False
_init_lock = asyncio.Lock()


def _dsn() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise ValueError("DATABASE_URL is empty")
    return value


def _connect():
    return psycopg2.connect(_dsn(), cursor_factory=RealDictCursor)


def _init_sync():
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS shared_exchange_requests (
                request_id BIGINT PRIMARY KEY,
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
                paid_at TIMESTAMP NULL
            )
            """)
            cur.execute("""
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
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_events_created ON shared_exchange_events(created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_events_type_created ON shared_exchange_events(event_type, created_at DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_shared_requests_created ON shared_exchange_requests(created_at DESC)")
            conn.commit()


async def ensure_supabase_sync_ready():
    global _inited
    if _inited:
        return
    async with _init_lock:
        if _inited:
            return
        await asyncio.to_thread(_init_sync)
        _inited = True


def _log_event_sync(event_type: str, request_id: int | None, user_id: int | None, username: str, profile_link: str, payload: dict):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shared_exchange_events (event_type, request_id, user_id, username, profile_link, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (event_type, request_id, user_id, username or "", profile_link or "", Json(payload or {})),
            )
            conn.commit()


async def sync_log_opened_exchange(user_id: int, username: str, profile_link: str):
    await ensure_supabase_sync_ready()
    await asyncio.to_thread(_log_event_sync, "opened_exchange", None, user_id, username, profile_link, {})


def _upsert_request_sync(
    request_id: int,
    user_id: int,
    username: str,
    profile_link: str,
    from_currency: str,
    to_currency: str,
    amount_from: float,
    amount_to: float,
    receive_details: str,
    payment_method: str,
    payment_submethod: str,
    status: str,
):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shared_exchange_requests
                (request_id, user_id, username, profile_link, from_currency, to_currency, amount_from, amount_to,
                 receive_details, payment_method, payment_submethod, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (request_id) DO UPDATE SET
                    user_id=EXCLUDED.user_id,
                    username=EXCLUDED.username,
                    profile_link=EXCLUDED.profile_link,
                    from_currency=EXCLUDED.from_currency,
                    to_currency=EXCLUDED.to_currency,
                    amount_from=EXCLUDED.amount_from,
                    amount_to=EXCLUDED.amount_to,
                    receive_details=EXCLUDED.receive_details,
                    payment_method=EXCLUDED.payment_method,
                    payment_submethod=EXCLUDED.payment_submethod,
                    status=EXCLUDED.status,
                    updated_at=NOW()
                """,
                (
                    request_id,
                    user_id,
                    username or "",
                    profile_link or "",
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
                    profile_link or "",
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


async def sync_log_request_created(**kwargs):
    await ensure_supabase_sync_ready()
    await asyncio.to_thread(_upsert_request_sync, **kwargs)


def _mark_paid_sync(
    request_id: int,
    user_id: int,
    username: str,
    profile_link: str,
    from_currency: str,
    to_currency: str,
    amount_from: float,
    amount_to: float,
    receive_details: str,
    payment_method: str,
):
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE shared_exchange_requests
                SET status='paid_pending_review', paid_at=NOW(), updated_at=NOW()
                WHERE request_id=%s
                """,
                (request_id,),
            )
            cur.execute(
                """
                INSERT INTO shared_exchange_events (event_type, request_id, user_id, username, profile_link, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    "paid",
                    request_id,
                    user_id,
                    username or "",
                    profile_link or "",
                    Json(
                        {
                            "from_currency": from_currency,
                            "to_currency": to_currency,
                            "amount_from": float(amount_from),
                            "amount_to": float(amount_to),
                            "receive_details": receive_details,
                            "payment_method": payment_method,
                        }
                    ),
                ),
            )
            conn.commit()


async def sync_mark_paid(**kwargs):
    await ensure_supabase_sync_ready()
    await asyncio.to_thread(_mark_paid_sync, **kwargs)


async def sync_log_qr_requested(request_id: int, user_id: int, username: str, profile_link: str, asset_name: str, target_value: str):
    await ensure_supabase_sync_ready()
    await asyncio.to_thread(
        _log_event_sync,
        "qr_requested",
        request_id,
        user_id,
        username,
        profile_link,
        {"asset_name": asset_name, "target_value": target_value},
    )


async def sync_log_wallet_urgent(
    request_id: int,
    user_id: int,
    username: str,
    profile_link: str,
    from_currency: str,
    to_currency: str,
    amount_from: float,
    amount_to: float,
    receive_details: str,
):
    await ensure_supabase_sync_ready()
    await asyncio.to_thread(
        _log_event_sync,
        "wallet_urgent",
        request_id,
        user_id,
        username,
        profile_link,
        {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount_from": float(amount_from),
            "amount_to": float(amount_to),
            "receive_details": receive_details,
        },
    )
