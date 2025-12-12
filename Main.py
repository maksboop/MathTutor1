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
    database.init_db()
    
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    # We don't use FSM storage right now, but it's here if you need it later
    storage = MemoryStorage() 
    dp = Dispatcher(storage=storage)

    # Include the router from handlers.py
    dp.include_router(router)

    # Start polling
    try:
        # The 'bot' argument is passed here in aiogram 3.x
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
