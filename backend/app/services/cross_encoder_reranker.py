import math
from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_model():
    # Lazy import: sentence_transformers pulls in torch, which takes seconds
    # to import. Only pay that when this backend is actually used.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.cross_encoder_model, max_length=512)


def warm_up() -> None:
    """Load the model at startup so the first chat request doesn't pay
    the load (or first-time download) cost."""
    _get_model()


def _sigmoid(x: float) -> float:
    # ms-marco cross-encoders output raw logits (e.g. 6.2 or -10.4).
    # Sigmoid maps them to a 0-1 relevance probability without changing
    # the ranking. Split form avoids math.exp overflow on large inputs.
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def rerank(question: str, candidates: list[dict], top_k: int | None = None) -> list[dict]:
    """Score every (question, chunk) pair and return the top_k most relevant,
    with relevance_score set to a 0-1 probability."""
    if not candidates:
        return []
    top_k = top_k or settings.rerank_top_k

    try:
        logits = _get_model().predict(
            [(question, c["text"]) for c in candidates],
            show_progress_bar=False,
        )
    except Exception as e:
        # Same graceful degradation as the LLM reranker: keep vector-search
        # order rather than failing the chat request.
        print(f"[cross_encoder] failed, using vector order: {e}")
        return candidates[:top_k]

    scored = [
        {**c, "relevance_score": _sigmoid(float(logit))}
        for c, logit in zip(candidates, logits)
    ]
    scored.sort(key=lambda c: c["relevance_score"], reverse=True)
    return scored[:top_k]
