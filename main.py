import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import load_config
from database import Database
from handlers.admin import get_admin_router
from handlers.user import get_user_router
from services.rates import RateService


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    db = Database(config.sqlite_path)
    db.init_db()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp["config"] = config
    dp["db"] = db
    dp["rate_service"] = RateService(config.coingecko_url, cache_ttl=config.rate_cache_ttl)

    dp.include_router(get_user_router())
    dp.include_router(get_admin_router())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
