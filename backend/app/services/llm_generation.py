"""
LLM answer generation, provider-switchable via settings.llm_provider.

Mirrors the pattern in embeddings.py: this is the only module that
knows which chat provider is configured. Callers just get a string
back from generate_answer().
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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def _generate_openai(system_prompt: str, user_prompt: str, model: str) -> str:
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,  # low temperature: we want grounded, consistent answers, not creativity
    )
    return response.choices[0].message.content


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def _generate_gemini(system_prompt: str, user_prompt: str, model: str) -> str:
    from google.genai import types

    client = _get_gemini_client()
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
        ),
    )
    return response.text


def generate_answer(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    """Generate a chat completion using whichever provider is configured."""
    chosen_model = model or settings.chat_model

    if settings.llm_provider == "gemini":
        return _generate_gemini(system_prompt, user_prompt, chosen_model)
    elif settings.llm_provider == "openai":
        return _generate_openai(system_prompt, user_prompt, chosen_model)
    else:
        raise ValueError(f"Unsupported llm_provider for generation: {settings.llm_provider}")