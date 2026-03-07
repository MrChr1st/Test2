import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    admin_ids: list
    support_username: str
    bot_username: str
    sqlite_path: str = "exchange_bot.db"


def load_config():
    token = os.getenv("BOT_TOKEN")

    admins = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x) for x in admins.split(",") if x]

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        support_username=os.getenv("SUPPORT_USERNAME", "@support"),
        bot_username=os.getenv("BOT_USERNAME", "bot"),
    )