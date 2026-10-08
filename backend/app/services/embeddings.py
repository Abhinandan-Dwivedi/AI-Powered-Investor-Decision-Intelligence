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


# Longer retry than OpenAI: the Gemini free tier allows ~100 embedded texts
# per minute, so a report with >100 chunks hits 429 on its second batch.
# Backoff of roughly 4+8+16+32+60s gives well over a minute of retrying,
# enough to outlast one quota window instead of failing the ingestion.
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
        # Gemini rejects batches over 100 texts (400 INVALID_ARGUMENT), so a
        # report with >100 chunks must be split. Batching here (not inside
        # _embed_gemini) means a retry only re-sends the batch that failed.
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
