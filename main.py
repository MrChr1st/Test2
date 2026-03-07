import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import load_config
from handlers.user import get_user_router


async def main():
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_router(get_user_router())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())