import os
import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
import io

load_dotenv()

# Загружаем промпт
try:
    with open('prompt.md', 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "Ты помощник по математике."

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.7,  # Чуть понизим для точности в математике
    "top_p": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Рекомендую использовать gemini-1.5-flash для скорости и работы с картинками
model = genai.GenerativeModel(
    model_name="gemini-3-pro-preview",
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT,
    safety_settings=safety_settings
)


async def get_gemini_response(chat_history: list, new_question: str) -> str:
    """Текстовый чат (как было раньше)."""
    try:
        convo = model.start_chat(history=chat_history)
        response = await convo.send_message_async(new_question)
        return response.text
    except Exception as e:
        print(f"Error Gemini Text: {e}")
        return "Ошибка нейросети. Попробуйте позже."


async def get_gemini_vision_response(image_bytes: bytes, user_caption: str) -> str:
    """Анализ изображения + текста."""
    try:
        # Превращаем байты в картинку PIL
        img = PIL.Image.open(io.BytesIO(image_bytes))

        # Если подписи нет, даем стандартную команду
        prompt = user_caption if user_caption else "Реши математическую задачу с этого изображения. Распиши решение подробно."

        # Отправляем картинку и текст (generate_content_async используется для 'разовых' запросов с картинками)
        response = await model.generate_content_async([prompt, img])
        return response.text
    except Exception as e:
        print(f"Error Gemini Vision: {e}")
        return "Не удалось обработать изображение. Убедитесь, что оно четкое."