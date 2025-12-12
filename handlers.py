from aiogram import Router, types, F
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
        f"Я ваш личный помощник по математике. Задайте мне любой вопрос.",
        reply_markup=main_keyboard() # You can remove this keyboard if it's not needed
    )

@router.message(F.text)
async def handle_text_message(message: types.Message):
    """Handles all text messages from the user."""
    user_id = message.from_user.id
    user_question = message.text

    # 1. Save user's message to the database
    database.add_message(user_id, 'user', user_question)

    # 2. Send a "thinking..." message
    thinking_message = await message.answer("Думаю...")

    # 3. Get chat history
    chat_history = database.get_chat_history(user_id)

    # 4. Get response from Gemini
    gemini_answer = await gemini.get_gemini_response(chat_history, user_question)

    # 5. Save Gemini's response to the database
    database.add_message(user_id, 'model', gemini_answer)

    # 6. Edit the "thinking..." message with the final answer
    await thinking_message.edit_text(gemini_answer, parse_mode="Markdown")

# You can remove the old help command or repurpose it later
# @router.message(Command(commands=['help']))
# async def help_command(message: types.Message):
#     """Sends a message when the /help command is issued."""
#     await message.answer('This is a help message.')
