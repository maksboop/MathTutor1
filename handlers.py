import io
from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from keyboards import main_keyboard
import database
import gemini

router = Router()

@router.message(CommandStart())
async def start(message: types.Message):
    """Handles the /start command, registers the user."""
    database.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        f"Я ваш личный помощник по математике. Задайте мне любой вопрос или отправьте фото задачи.",
        reply_markup=main_keyboard()
    )

async def process_and_respond(message: types.Message, user_question: str, image_data: bytes | None = None):
    """
    A helper function to process user's request (text or image) and send it to Gemini.
    """
    user_id = message.from_user.id

    # 1. Save user's message to the database
    # For images, we save a placeholder text.
    db_content = user_question
    if image_data:
        # We don't store the image, just the caption and a placeholder
        db_content = f"[Изображение] {user_question}".strip()
    database.add_message(user_id, 'user', db_content)

    # 2. Send a "thinking..." message
    thinking_message = await message.answer("Думаю...")

    # 3. Get chat history
    chat_history = database.get_chat_history(user_id)

    # 4. Get response from Gemini
    gemini_answer = await gemini.get_gemini_response(chat_history, user_question, image_data)

    # 5. Save Gemini's response to the database
    database.add_message(user_id, 'model', gemini_answer)

    # 6. Edit the "thinking..." message with the final answer
    # Use a try-except block in case the message contains characters not supported by Markdown
    try:
        await thinking_message.edit_text(gemini_answer, parse_mode="Markdown")
    except Exception:
        await thinking_message.edit_text(gemini_answer)


@router.message(F.text)
async def handle_text_message(message: types.Message):
    """Handles all text messages from the user."""
    await process_and_respond(message, message.text)


@router.message(F.photo)
async def handle_photo_message(message: types.Message, bot: Bot):
    """Handles messages with photos."""
    # Download the photo into a bytes buffer
    # message.photo[-1] is the largest version of the photo
    photo_file = await bot.get_file(message.photo[-1].file_id)
    image_bytes_io = await bot.download_file(photo_file.file_path)
    image_data = image_bytes_io.read()

    # The user's question can be in the caption
    user_question = message.caption if message.caption else ""

    await process_and_respond(message, user_question, image_data)
