from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard():
    """Creates the main keyboard with user-friendly buttons."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧹 Начать заново"),
                KeyboardButton(text="📚 Справка")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши вопрос или отправь фото..."
    )
