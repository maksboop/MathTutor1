from aiogram import Router, types, F
from aiogram.filters import CommandStart
from keyboards import main_keyboard
import database
import gemini
import io
router = Router()

@router.message(CommandStart())
async def start(message: types.Message):
    """Handles the /start command, registers the user."""
    # ДОБАВЛЕН AWAIT
    await database.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        f"Я ваш личный помощник по математике. Задайте мне любой вопрос.",
        reply_markup=main_keyboard()
    )

@router.message(F.text)
async def handle_text_message(message: types.Message):
    """Handles all text messages from the user."""
    user_id = message.from_user.id
    user_question = message.text

    # 1. Save user's message to the database
    # ДОБАВЛЕН AWAIT
    await database.add_message(user_id, 'user', user_question)

    # 2. Send a "thinking..." message
    thinking_message = await message.answer("Думаю...")

    # 3. Get chat history
    # ДОБАВЛЕН AWAIT
    chat_history = await database.get_chat_history(user_id)

    # 4. Get response from Gemini
    gemini_answer = await gemini.get_gemini_response(chat_history, user_question)

    # 5. Save Gemini's response to the database
    # ДОБАВЛЕН AWAIT
    await database.add_message(user_id, 'model', gemini_answer)

    # 6. Edit the "thinking..." message with the final answer
    await thinking_message.edit_text(gemini_answer, parse_mode="Markdown")


@router.message(F.photo)
async def handle_photo_message(message: types.Message):
    """Обрабатывает изображения с задачами."""
    user_id = message.from_user.id
    # Если есть подпись к фото, берем её, иначе стандартный текст
    user_caption = message.caption if message.caption else ""

    # 1. Сохраняем факт отправки фото в историю (текстом)
    log_text = f"[Отправил фото] {user_caption}"
    await database.add_message(user_id, 'user', log_text)

    # 2. Сообщение "Думаю..."
    thinking_message = await message.answer("Изучаю изображение... 🖼️")

    try:
        # 3. Скачиваем фото в память (BytesIO)
        bot = message.bot
        # Берем последнее фото из массива (оно самого высокого качества)
        photo = message.photo[-1]

        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()

        # 4. Отправляем в Gemini
        gemini_answer = await gemini.get_gemini_vision_response(image_bytes, user_caption)

        # 5. Сохраняем ответ и отправляем пользователю
        await database.add_message(user_id, 'model', gemini_answer)
        await thinking_message.edit_text(gemini_answer, parse_mode="Markdown")

    except Exception as e:
        await thinking_message.edit_text("Произошла ошибка при загрузке фото.")
        print(f"Photo Handler Error: {e}")