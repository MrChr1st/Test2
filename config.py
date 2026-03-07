import os
from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    bot_token: str
    admin_ids: List[int]
    bot_username: str
    support_username: str
    sqlite_path: str
    fee: float
    referral_fee_discount_per_user: float
    max_referral_fee_discount: float
    coingecko_url: str
    frankfurter_url: str
    rate_cache_ttl: int
    sbp_payment_url: str
    card_number: str
    bybit_id: str
    report_bot_token: str
    report_chat_id: str


def parse_admin_ids(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is empty")

    return Config(
        bot_token=token,
        admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        bot_username=os.getenv("BOT_USERNAME", "Ccchangerrr_bot").strip(),
        support_username=os.getenv("SUPPORT_USERNAME", "@eeexxxchangerrr").strip(),
        sqlite_path=os.getenv("SQLITE_PATH", "exchange_bot.db").strip(),
        fee=float(os.getenv("FEE", "0.0095")),
        referral_fee_discount_per_user=float(os.getenv("REFERRAL_FEE_DISCOUNT_PER_USER", "0.002")),
        max_referral_fee_discount=float(os.getenv("MAX_REFERRAL_FEE_DISCOUNT", "0.0095")),
        coingecko_url=os.getenv("COINGECKO_URL", "https://api.coingecko.com/api/v3/simple/price").strip(),
        frankfurter_url=os.getenv("FRANKFURTER_URL", "https://api.frankfurter.dev/v1/latest").strip(),
        rate_cache_ttl=int(os.getenv("RATE_CACHE_TTL", "60")),
        sbp_payment_url=os.getenv("SBP_PAYMENT_URL", "https://www.donationalerts.com/r/eeexchanger").strip(),
        card_number=os.getenv("CARD_NUMBER", "5599002046385292").strip(),
        bybit_id=os.getenv("BYBIT_ID", "204479397").strip(),
        report_bot_token=os.getenv("REPORT_BOT_TOKEN", "").strip(),
        report_chat_id=os.getenv("REPORT_CHAT_ID", "").strip(),
    )