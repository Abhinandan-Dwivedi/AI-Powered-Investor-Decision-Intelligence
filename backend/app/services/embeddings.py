from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings 

_openai_client = None
_gemini_client = None

# Hard API limit on texts per Gemini embed_content request.
_GEMINI_MAX_BATCH = 100


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai

        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20))
def _embed_openai(texts: list[str]) -> list[list[float]]:
    client = _get_openai_client()
    response = client.embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]


@retry(stop=stop_after_attempt(6), wait=wait_exponential(multiplier=2, min=4, max=60))
def _embed_gemini(texts: list[str]) -> list[list[float]]:
    from google.genai import types

    client = _get_gemini_client()
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.embedding_dimensions,
        ),
    )
    return [e.values for e in result.embeddings]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using whichever provider is configured."""
    if not texts:
        return []

    if settings.llm_provider == "gemini":
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _GEMINI_MAX_BATCH):
            vectors.extend(_embed_gemini(texts[start : start + _GEMINI_MAX_BATCH]))
        return vectors
    elif settings.llm_provider == "openai":
        return _embed_openai(texts)
    else:
        raise ValueError(f"Unsupported llm_provider for embeddings: {settings.llm_provider}")


def embed_query(text: str) -> list[float]:
    """Embed a single query string (used at retrieval time)."""
    return embed_texts([text])[0]
