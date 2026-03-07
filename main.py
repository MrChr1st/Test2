import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import load_config
from database import Database
from handlers.admin import get_admin_router
from handlers.user import get_user_router
from services.calculator import CalculatorService
from services.rates import RateService


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    db = Database(config.sqlite_path)
    rate_service = RateService(config.coingecko_url)
    calculator = CalculatorService(config.fee, config.client_bonus)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(get_user_router(db, rate_service, calculator, config.admin_ids))
    dp.include_router(get_admin_router(db, config.admin_ids))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
