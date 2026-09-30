import sys
sys.path.insert(0, ".")

from app.core.config import settings
print("Chat model:", settings.chat_model)

from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)

try:
    response = client.models.generate_content(
        model=settings.chat_model,
        contents="Say hello in one sentence.",
        config=types.GenerateContentConfig(
            system_instruction="You are a helpful assistant.",
            temperature=0.2,
        ),
    )
    print("SUCCESS:", response.text)
except Exception as e:
    print("REAL ERROR TYPE:", type(e).__name__)
    print("REAL ERROR MESSAGE:", str(e))