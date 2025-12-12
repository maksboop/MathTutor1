from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    """Creates the main keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='/start'), KeyboardButton(text='/help')],
            [KeyboardButton(text='/clear')] # <-- Новая кнопка
        ],
        resize_keyboard=True
    )