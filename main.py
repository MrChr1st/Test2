import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from database import Database
from handlers import router
from services import RateService

async def main():
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp["config"] = config
    dp["db"] = Database(config.sqlite_path)
    dp["rate_service"] = RateService(config.coingecko_url, config.frankfurter_url, config.rate_cache_ttl)

    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
