import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    fee: float = 0.0
    client_bonus: float = 1.02
    sqlite_path: str = "exchange_bot.db"
    coingecko_url: str = "https://api.coingecko.com/api/v3/simple/price"
    support_username: str = "@support"
    bot_username: str = "your_bot_username"
    referral_bonus_text_ru: str = "За каждого приглашенного пользователя вы можете получить индивидуальный бонус."
    referral_bonus_text_en: str = "You can receive a custom bonus for each invited user."
    rate_cache_ttl: int = 60


def parse_admin_ids(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is empty. Set a real token in .env")
    admin_ids = parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise ValueError("ADMIN_IDS is empty. Set at least one Telegram user ID in .env")
    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        fee=float(os.getenv("FEE", "0.0").strip()),
        client_bonus=float(os.getenv("CLIENT_BONUS", "1.02").strip()),
        sqlite_path=os.getenv("SQLITE_PATH", "exchange_bot.db").strip(),
        coingecko_url=os.getenv("COINGECKO_URL", "https://api.coingecko.com/api/v3/simple/price").strip(),
        support_username=os.getenv("SUPPORT_USERNAME", "@support").strip(),
        bot_username=os.getenv("BOT_USERNAME", "your_bot_username").strip().lstrip("@"),
        referral_bonus_text_ru=os.getenv("REFERRAL_BONUS_TEXT_RU", "За каждого приглашенного пользователя вы можете получить индивидуальный бонус.").strip(),
        referral_bonus_text_en=os.getenv("REFERRAL_BONUS_TEXT_EN", "You can receive a custom bonus for each invited user.").strip(),
        rate_cache_ttl=int(os.getenv("RATE_CACHE_TTL", "60").strip()),
    )
