import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    fee: float = 0.012
    client_bonus: float = 1.01
    sqlite_path: str = "exchange_bot.db"
    coingecko_url: str = "https://api.coingecko.com/api/v3/simple/price"


def _parse_admin_ids(raw: str) -> List[int]:
    result: List[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            result.append(int(item))
        except ValueError as exc:
            raise ValueError(f"ADMIN_IDS contains invalid integer: {item}") from exc
    return result


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is empty. Put your real bot token into .env")

    if ":" not in bot_token:
        raise ValueError("BOT_TOKEN looks invalid. Telegram bot token must contain ':'")

    return Config(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        fee=float(os.getenv("FEE", "0.012")),
        client_bonus=float(os.getenv("CLIENT_BONUS", "1.01")),
        sqlite_path=os.getenv("SQLITE_PATH", "exchange_bot.db").strip() or "exchange_bot.db",
        coingecko_url=(
            os.getenv(
                "COINGECKO_URL",
                "https://api.coingecko.com/api/v3/simple/price",
            ).strip()
            or "https://api.coingecko.com/api/v3/simple/price"
        ),
    )
