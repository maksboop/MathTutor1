import io
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command  # 1. Импортируем Command
from keyboards import main_keyboard
import database
import gemini

router = Router()


# --- 1. Сначала команды и специальные фильтры ---

@router.message(CommandStart())
async def start(message: types.Message):
    """Handles the /start command, registers the user."""
    await database.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        f"Я ваш личный помощник по математике. Задайте мне любой вопрос или отправьте фото задачи.",
        reply_markup=main_keyboard()
    )


@router.message(Command("clear"))  # 2. Команда clear должна быть ДО F.text
async def cmd_clear(message: types.Message):
    """Очищает историю диалога."""
    await database.clear_history(message.from_user.id)
    await message.answer(
        "История переписки очищена! 🧹\n"
        "Я забыл контекст предыдущих задач. Можем начать новую тему!",
        reply_markup=main_keyboard()
    )


@router.message(F.photo)
async def handle_photo_message(message: types.Message):
    """Обрабатывает изображения с задачами."""
    user_id = message.from_user.id
    user_caption = message.caption if message.caption else ""

    log_text = f"[Отправил фото] {user_caption}"
    await database.add_message(user_id, 'user', log_text)

    thinking_message = await message.answer("Изучаю изображение... 🖼️")

    try:
        bot = message.bot
        photo = message.photo[-1]

        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()

        gemini_answer = await gemini.get_gemini_vision_response(image_bytes, user_caption)

        await database.add_message(user_id, 'model', gemini_answer)
        await thinking_message.edit_text(gemini_answer, parse_mode="Markdown")

    except Exception as e:
        await thinking_message.edit_text("Произошла ошибка при загрузке фото.")
        print(f"Photo Handler Error: {e}")


# --- 2. В самом конце общий обработчик текста ---

@router.message(F.text)
async def handle_text_message(message: types.Message):
    """Handles all text messages from the user."""
    user_id = message.from_user.id
    user_question = message.text

    # 1. Save user's message
    await database.add_message(user_id, 'user', user_question)

    # 2. Send "thinking..."
    thinking_message = await message.answer("Думаю...")

    # 3. Get chat history (с лимитом)
    chat_history = await database.get_chat_history(user_id)

    # 4. Get response from Gemini
    gemini_answer = await gemini.get_gemini_response(chat_history, user_question)

    # 5. Save response
    await database.add_message(user_id, 'model', gemini_answer)

    # 6. Edit message
    await thinking_message.edit_text(gemini_answer, parse_mode="Markdown")