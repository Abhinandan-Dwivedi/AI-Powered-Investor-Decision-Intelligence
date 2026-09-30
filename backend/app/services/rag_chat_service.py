"""
RAG chat orchestration: embed question -> vector search -> rerank ->
build grounded prompt -> generate answer.

This is the query-time half of the RAG pipeline (the ingestion service
is the other half). Kept as its own module so the router stays a thin
HTTP wrapper and this logic can be tested/reused independently (e.g.
from a CLI script or the eval harness we'll build later).
"""
from app.core.config import settings
from app.services.embeddings import embed_query
from app.services.llm_generation import generate_answer
from app.services.reranker import rerank
from app.services.vector_store import search as vector_search

CHAT_SYSTEM_PROMPT = """You are a financial analyst assistant. Answer the \
user's question using ONLY the provided context chunks from company \
financial reports. If the context does not contain enough information to \
answer confidently, say so explicitly rather than guessing or using outside \
knowledge. Cite which company and fiscal year each fact comes from when \
relevant. Keep answers concise and precise — this is for investors who want \
accurate numbers, not filler."""


def answer_question(
    question: str,
    company: str | None = None,
    fiscal_year: int | None = None,
    use_reranking: bool = True,
) -> dict:
    """Returns {"answer": str, "sources": list[dict]}.

    use_reranking exists specifically so the eval harness can A/B test
    the reranking step's actual impact — set it False to take the raw
    top-N vector search results directly, bypassing the LLM rerank call.
    """

    # 1. Embed the question with the SAME embedding model used at ingestion —
    #    mixing embedding models between ingestion and query would produce
    #    vectors that aren't comparable, silently breaking retrieval.
    query_vector = embed_query(question)

    # 2. Vector search, optionally scoped to a specific company/year.
    raw_results = vector_search(
        query_vector=query_vector,
        company=company,
        fiscal_year=fiscal_year,
        top_k=settings.retrieval_top_k,
    )

    if not raw_results:
        return {
            "answer": "I couldn't find any relevant information in the ingested documents to answer that question.",
            "sources": [],
        }

    candidates = [
        {
            "text": r.payload["text"],
            "company": r.payload["company"],
            "fiscal_year": r.payload["fiscal_year"],
            "source_file": r.payload["source_file"],
            "relevance_score": r.score,  # raw vector similarity score, used when reranking is skipped
        }
        for r in raw_results
    ]

    if use_reranking:
        # 3a. Rerank: narrow from retrieval_top_k (broad recall) down to
        #     rerank_top_k (precise, actually-relevant chunks) before they
        #     ever reach the LLM's context window.
        top_chunks = rerank(question, candidates, top_k=settings.rerank_top_k)
    else:
        # 3b. Bypass path for the A/B test: just take the top-N by raw
        #     vector similarity score, no LLM rerank call at all.
        top_chunks = candidates[: settings.rerank_top_k]

    # 4. Build the grounded prompt from only the reranked, relevant chunks.
    context_block = "\n\n---\n\n".join(
        f"[{c['company']} FY{c['fiscal_year']}]: {c['text']}" for c in top_chunks
    )
    user_prompt = f"Context:\n{context_block}\n\nQuestion: {question}"

    answer = generate_answer(system_prompt=CHAT_SYSTEM_PROMPT, user_prompt=user_prompt)

    return {
        "answer": answer,
        "sources": [
            {
                "text": c["text"],
                "company": c["company"],
                "fiscal_year": c["fiscal_year"],
                "source_file": c["source_file"],
                "relevance_score": c["relevance_score"],
            }
            for c in top_chunks
        ],
    }