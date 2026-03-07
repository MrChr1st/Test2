import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    support_username: str
    bot_username: str
    sqlite_path: str = "exchange_bot.db"
    fee: float = 0.0095
    referral_fee_discount_per_user: float = 0.002
    max_referral_fee_discount: float = 0.0095
    coingecko_url: str = "https://api.coingecko.com/api/v3/simple/price"
    frankfurter_url: str = "https://api.frankfurter.dev/v1/latest"
    rate_cache_ttl: int = 60
    card_payment_url: str = "https://example.com/card"
    sbp_payment_url: str = "https://www.donationalerts.com/r/eeexchanger"
    crypto_payment_url: str = "https://example.com/crypto"
    card_number: str = "5599 0020 4638 5292"


def parse_admin_ids(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is empty")

    return Config(
        bot_token=token,
        admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        support_username=os.getenv("SUPPORT_USERNAME", "@eeexxxchangerrr").strip(),
        bot_username=os.getenv("BOT_USERNAME", "Ccchangerrr_bot").strip(),
        sqlite_path=os.getenv("SQLITE_PATH", "exchange_bot.db").strip(),
        fee=float(os.getenv("FEE", "0.0095")),
        referral_fee_discount_per_user=float(os.getenv("REFERRAL_FEE_DISCOUNT_PER_USER", "0.002")),
        max_referral_fee_discount=float(os.getenv("MAX_REFERRAL_FEE_DISCOUNT", "0.0095")),
        coingecko_url=os.getenv("COINGECKO_URL", "https://api.coingecko.com/api/v3/simple/price").strip(),
        frankfurter_url=os.getenv("FRANKFURTER_URL", "https://api.frankfurter.dev/v1/latest").strip(),
        rate_cache_ttl=int(os.getenv("RATE_CACHE_TTL", "60")),
        card_payment_url=os.getenv("CARD_PAYMENT_URL", "https://example.com/card").strip(),
        sbp_payment_url=os.getenv("SBP_PAYMENT_URL", "https://www.donationalerts.com/r/eeexchanger").strip(),
        crypto_payment_url=os.getenv("CRYPTO_PAYMENT_URL", "https://example.com/crypto").strip(),
        card_number=os.getenv("CARD_NUMBER", "5599 0020 4638 5292").strip(),
    )
