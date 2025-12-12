import io
from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction, ParseMode
from aiogram.utils.chat_action import ChatActionSender
from keyboards import main_keyboard
import database
import gemini

router = Router()

@router.message(CommandStart())
async def start(message: types.Message):
    """Handles the /start command, registers the user."""
    await database.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n"
        f"Я ваш личный помощник по математике. Задайте мне любой вопрос или отправьте фото задачи.",
        reply_markup=main_keyboard()
    )

@router.message(F.text == "📚 Справка")
@router.message(Command('help'))
async def help_command(message: types.Message):
    """Sends a help message."""
    help_text = (
        "<b>Справка</b>\n\n"
        "Я — ваш персональный репетитор по математике. Моя цель — не просто дать ответ, а научить вас решать задачи.\n\n"
        "<b>Что я умею:</b>\n"
        "🔹 <b>Решать по фото:</b> Отправьте фотографию уравнения или задачи из учебника.\n"
        "🔹 <b>Пошаговые объяснения:</b> Я расписываю решение подробно, чтобы вы поняли логику.\n"
        "🔹 <b>Теория:</b> Могу объяснить математические термины и теоремы.\n\n"
        "<b>Как пользоваться:</b>\n"
        "Просто напишите вопрос или прикрепите картинку. Если что-то непонятно в решении, смело переспрашивайте!\n"
        "Используйте кнопку '🧹 Начать заново', чтобы очистить историю и начать новую тему."
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "🧹 Начать заново")
@router.message(Command('clear'))
async def clear_command(message: types.Message):
    """Clears the user's chat history."""
    await database.clear_history(message.from_user.id)
    await message.answer("Ваша история сообщений очищена. Можете начать новую тему.")

async def process_and_respond(message: types.Message, user_question: str, image_data: bytes | None = None):
    """
    A helper function to process user's request (text or image) and send it to Gemini.
    """
    user_id = message.from_user.id
    
    # Send initial placeholder
    thinking_message = await message.answer("⏳ Анализирую задачу...")

    gemini_answer = ""
    db_content = user_question

    # Determine action type
    action_type = ChatAction.UPLOAD_PHOTO if image_data else ChatAction.TYPING

    # Use ChatActionSender to keep the status active automatically
    async with ChatActionSender(bot=message.bot, chat_id=message.chat.id, action=action_type):
        if image_data:
            db_content = f"[Изображение] {user_question}".strip()
            # Add user message to DB
            await database.add_message(user_id, 'user', db_content)
            # Get response
            gemini_answer = await gemini.get_gemini_vision_response(image_data, user_question)
        else:
            # Add user message to DB
            await database.add_message(user_id, 'user', db_content)
            # Get history
            chat_history = await database.get_chat_history(user_id)
            # Get response
            gemini_answer = await gemini.get_gemini_response(chat_history, user_question)
            
        # Save model response to DB
        await database.add_message(user_id, 'model', gemini_answer)

    # Edit the message with the result
    try:
        await thinking_message.edit_text(gemini_answer, parse_mode=ParseMode.HTML)
    except Exception:
        # Fallback if HTML is broken
        await thinking_message.edit_text(gemini_answer)

@router.message(F.text)
async def handle_text_message(message: types.Message):
    """Handles all text messages from the user."""
    if message.text not in ["📚 Справка", "🧹 Начать заново"]:
        await process_and_respond(message, message.text)

@router.message(F.photo)
async def handle_photo_message(message: types.Message, bot: Bot):
    """Handles messages with photos."""
    photo_file = await bot.get_file(message.photo[-1].file_id)
    image_bytes_io = await bot.download_file(photo_file.file_path)
    image_data = image_bytes_io.read()
    user_question = message.caption if message.caption else ""
    await process_and_respond(message, user_question, image_data=image_data)
