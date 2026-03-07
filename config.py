
import os
from dataclasses import dataclass

@dataclass
class Config:
    bot_token:str
    admin_ids:list
    support_username:str
    bot_username:str
    sqlite_path:str="exchange_bot.db"
    fee:float=0.0095
    referral_fee_discount_per_user:float=0.002
    max_referral_fee_discount:float=0.0095
    coingecko_url:str="https://api.coingecko.com/api/v3/simple/price"
    frankfurter_url:str="https://api.frankfurter.dev/v1/latest"
    rate_cache_ttl:int=60
    card_number:str="5599 0020 4638 5292"

def load_config():
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        admin_ids=[int(os.getenv("ADMIN_IDS","0"))],
        support_username=os.getenv("SUPPORT_USERNAME","@eeexxxchangerrr"),
        bot_username=os.getenv("BOT_USERNAME","Ccchangerrr_bot")
    )
