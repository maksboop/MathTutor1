import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import router
import database

load_dotenv()


async def main():
    """Start the bot."""
    # Initialize the database
    # ДОБАВЛЕН AWAIT
    await database.init_db()

    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())