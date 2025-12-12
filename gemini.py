import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Load the system prompt from the file
with open('prompt.md', 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT = f.read()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Set up the model
generation_config = {
    "temperature": 0.5, # Lower temperature for more precise math
    "top_p": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Using gemini-1.5-flash as it is fast and multimodal (supports images)
model = genai.GenerativeModel(
    model_name="gemini-3-pro-preview",
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT,
    safety_settings=safety_settings
)

async def get_gemini_response(chat_history: list, new_question: str, image_data: bytes = None) -> str:
    """
    Gets a response from the Gemini API.
    'chat_history' should be a list of dictionaries from the database.
    'image_data' is optional bytes of the image.
    """
    try:
        # Start the chat with history
        convo = model.start_chat(history=chat_history)
        
        if image_data:
            # If there is an image, we send it along with the text
            # We create a list of content parts
            content = [
                new_question if new_question else "Что изображено на картинке? Реши эту задачу.",
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ]
            await convo.send_message_async(content)
        else:
            # Text only
            await convo.send_message_async(new_question)
            
        return convo.last.text
    except Exception as e:
        print(f"Error getting response from Gemini: {e}")
        return f"Извините, произошла ошибка при обращении к нейросети: {e}"
