import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

from handlers import router
import database

load_dotenv()

async def set_bot_commands(bot: Bot):
    """Sets the bot's commands in the Telegram menu."""
    commands = [
        BotCommand(command="/start", description="🚀 Перезапустить бота"),
        BotCommand(command="/help", description="📚 Справка"),
        BotCommand(command="/clear", description="🧹 Начать новую тему")
    ]
    await bot.set_my_commands(commands)

async def main():
    """Start the bot."""
    # Initialize the database
    await database.init_db()

    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(router)

    # Set the commands in the menu
    await set_bot_commands(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
