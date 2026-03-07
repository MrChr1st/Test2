import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    fee: float = 0.012
    client_bonus: float = 1.02
    sqlite_path: str = "exchange_bot.db"
    coingecko_url: str = "https://api.coingecko.com/api/v3/simple/price"
    support_username: str = "@your_support"


def parse_admin_ids(raw: str) -> List[int]:
    ids = []
    for item in raw.split(","):
        item = item.strip()
        if item:
            ids.append(int(item))
    return ids


def load_config() -> Config:
    return Config(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        fee=float(os.getenv("FEE", "0.012")),
        client_bonus=float(os.getenv("CLIENT_BONUS", "1.02")),
        sqlite_path=os.getenv("SQLITE_PATH", "exchange_bot.db").strip(),
        coingecko_url=os.getenv(
            "COINGECKO_URL",
            "https://api.coingecko.com/api/v3/simple/price",
        ).strip(),
        support_username=os.getenv("SUPPORT_USERNAME", "@your_support").strip(),
    )