import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
import PIL.Image
import io

load_dotenv()

try:
    with open('prompt.md', 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are a helpful math tutor. Please format your answers using only supported Telegram HTML tags (<b>, <i>, <code>, <pre>)."

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.5,
    "top_p": 1,
    "max_output_tokens": 4096,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-3-pro-preview",
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT,
    safety_settings=safety_settings
)

def sanitize_response(text: str) -> str:
    """
    A robust sanitizer for Telegram HTML.
    """
    # 0. Convert Markdown bold/italic to HTML (Common fallback)
    # Replace **text** with <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Replace __text__ with <i>text</i>
    text = re.sub(r'__(.*?)__', r'<i>\1</i>', text)
    # Replace `text` with <code>text</code> (if not already inside code tag)
    # This is tricky with regex, so we do a simple pass:
    # We assume if we see backticks, it's code.
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # 1. Replace common unsupported block tags with newlines/bold
    text = re.sub(r'<h[1-6]>', '\n<b>', text)
    text = re.sub(r'</h[1-6]>', '</b>\n', text)
    text = text.replace('<hr>', '\n' + '—' * 15 + '\n')
    text = text.replace('<br>', '\n')
    text = text.replace('<p>', '\n')
    text = text.replace('</p>', '\n')
    
    # 2. Remove all other tags EXCEPT the allowed ones
    # Allowed: b, strong, i, em, u, ins, s, strike, del, code, pre, blockquote
    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'code', 'pre', 'blockquote']
    
    # This regex matches any tag </?tagName...>
    def tag_replacer(match):
        tag_content = match.group(0)
        # Extract tag name
        tag_name_match = re.match(r'</?([a-zA-Z0-9]+)', tag_content)
        if tag_name_match:
            tag_name = tag_name_match.group(1).lower()
            if tag_name in allowed_tags:
                return tag_content # Keep allowed tag
        return "" # Remove unsupported tag

    text = re.sub(r'</?[a-zA-Z0-9]+[^>]*>', tag_replacer, text)

    # 3. Fix unclosed tags (simple heuristic)
    if text.count('<code>') > text.count('</code>'):
        text += '</code>'
    if text.count('<pre>') > text.count('</pre>'):
        text += '</pre>'
    if text.count('<b>') > text.count('</b>'):
        text += '</b>'
        
    return text.strip()

async def get_gemini_response(chat_history: list, new_question: str) -> str:
    """Text-based chat."""
    try:
        convo = model.start_chat(history=chat_history)
        response = await convo.send_message_async(new_question)
        sanitized_text = sanitize_response(response.text)
        return sanitized_text
    except Exception as e:
        print(f"Error Gemini Text: {e}")
        return f"<b>Ошибка нейросети:</b>\n<code>{e}</code>"

async def get_gemini_vision_response(image_bytes: bytes, user_caption: str) -> str:
    """Image analysis + text."""
    try:
        img = PIL.Image.open(io.BytesIO(image_bytes))
        prompt = user_caption if user_caption else "Реши математическую задачу с этого изображения. Распиши решение подробно."
        response = await model.generate_content_async([prompt, img])
        sanitized_text = sanitize_response(response.text)
        return sanitized_text
    except Exception as e:
        print(f"Error Gemini Vision: {e}")
        return f"<b>Не удалось обработать изображение.</b>\nУбедитесь, что оно четкое.\n<code>{e}</code>"
