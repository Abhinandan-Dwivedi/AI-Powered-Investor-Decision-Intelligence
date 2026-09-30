import sys
sys.path.insert(0, ".")

from app.core.config import settings
print("Provider:", settings.llm_provider)
print("Embedding model:", settings.embedding_model)
print("Gemini key set:", bool(settings.gemini_api_key), "len:", len(settings.gemini_api_key or ""))

from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)

try:
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=["test sentence"],
        config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimensions),
    )
    print("SUCCESS:", len(result.embeddings[0].values), "dims")
except Exception as e:
    print("REAL ERROR TYPE:", type(e).__name__)
    print("REAL ERROR MESSAGE:", str(e))