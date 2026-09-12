"""
Embedding generation, provider-switchable via settings.llm_provider.

Design note: this module is the ONLY place that knows which embedding
provider we're using. Every other module (ingestion, retrieval) just
calls embed_texts()/embed_query() and gets back plain float lists —
swapping providers here never requires touching calling code.

Gemini is the default because Google AI Studio offers a genuinely
free, rate-limited tier (no prepaid credit required), which is
friendlier for development than OpenAI's current pay-first model.
"""
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

_openai_client = None
_gemini_client = None


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


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20))
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
        return _embed_gemini(texts)
    elif settings.llm_provider == "openai":
        return _embed_openai(texts)
    else:
        raise ValueError(f"Unsupported llm_provider for embeddings: {settings.llm_provider}")


def embed_query(text: str) -> list[float]:
    """Embed a single query string (used at retrieval time)."""
    return embed_texts([text])[0]
