"""
Reranking: takes the top-K vector search results and re-scores them
for actual relevance to the question, keeping only the best few.

Why this matters: vector similarity search finds chunks that are
SEMANTICALLY CLOSE to the query, which isn't the same as "most useful
to answer this exact question." Two sections about "gross margin" can
sit close together in embedding space even if only one actually
answers a specific question about margin change year-over-year.

We use an LLM-as-reranker here (cheap Gemini/OpenAI call scoring each
chunk 0-10) rather than a dedicated cross-encoder model, to avoid a
heavy PyTorch dependency for a project at this scale. At larger scale,
swapping this for a proper cross-encoder (e.g. BAAI/bge-reranker)
would be the natural upgrade — same interface, different internals.
"""
import json
import re

from app.core.config import settings
from app.services.llm_generation import generate_answer

RERANK_SYSTEM_PROMPT = """You are a relevance-scoring engine for a financial \
document retrieval system. Given a user question and a list of text chunks, \
score each chunk from 0 to 10 on how directly useful it is for answering the \
question. A chunk that contains the exact fact needed scores high (8-10). A \
chunk that is topically related but doesn't answer the question scores low \
(0-3). Respond ONLY with a JSON array of integers, one score per chunk, in \
the same order as given. Example: [8, 2, 5]"""


def rerank(question: str, candidates: list[dict], top_k: int | None = None) -> list[dict]:
    """
    candidates: list of dicts, each with at least a "text" key (chunk content).
    Returns the same dicts, sorted by relevance, truncated to top_k, with a
    "relevance_score" key added.
    """
    if not candidates:
        return []

    top_k = top_k or settings.rerank_top_k

    numbered_chunks = "\n\n".join(
        f"[{i}] {c['text'][:600]}" for i, c in enumerate(candidates)
    )
    user_prompt = f"Question: {question}\n\nChunks:\n{numbered_chunks}"

    try:
        raw_response = generate_answer(
            system_prompt=RERANK_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=settings.chat_model,
        )
        scores = _parse_score_array(raw_response, expected_length=len(candidates))
    except Exception:
        # Reranking is an enhancement, not a hard dependency — if the LLM
        # call or parsing fails, fall back to original vector-search order
        # (assigning a neutral score) rather than breaking the chat request.
        scores = [5.0] * len(candidates)

    scored = [
        {**candidate, "relevance_score": score}
        for candidate, score in zip(candidates, scores)
    ]
    scored.sort(key=lambda c: c["relevance_score"], reverse=True)
    return scored[:top_k]


def _parse_score_array(raw_text: str, expected_length: int) -> list[float]:
    """Extract a JSON array of numbers from the LLM's response, tolerating
    minor formatting noise (e.g. markdown code fences)."""
    match = re.search(r"\[[\d,\s.]+\]", raw_text)
    if not match:
        raise ValueError(f"No score array found in reranker output: {raw_text!r}")

    scores = json.loads(match.group(0))
    if len(scores) != expected_length:
        raise ValueError(
            f"Reranker returned {len(scores)} scores, expected {expected_length}"
        )
    return [float(s) for s in scores]