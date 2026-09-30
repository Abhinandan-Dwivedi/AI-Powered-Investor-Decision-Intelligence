"""
A/B test: runs the golden question set through the RAG pipeline twice —
once WITH the LLM reranking step, once WITHOUT (raw vector search order
only) — and compares retrieval hit rate + keyword coverage side by
side.

This answers a concrete question: "is the reranking step actually
helping, and by how much?" — rather than assuming it does because it's
architecturally sensible.

Run from the backend/ directory (needs live Postgres/Qdrant/LLM key,
and documents matching golden_dataset.py already ingested):

    python -m eval.run_reranking_ab_test
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.golden_dataset import GOLDEN_QUESTIONS
from eval.metrics import keyword_coverage, retrieval_hit
from app.services.rag_chat_service import answer_question


def _run_condition(use_reranking: bool) -> list[dict]:
    results = []
    for case in GOLDEN_QUESTIONS:
        try:
            result = answer_question(case["question"], use_reranking=use_reranking)
        except Exception as e:
            print(f"  [ERROR] \"{case['question']}\": {e}")  # was silently swallowed before — now visible
            results.append({**case, "retrieval_hit": False, "keyword_coverage": 0.0, "error": str(e)})
            continue

        # Debug visibility: show exactly what came back, so a 0% hit rate
        # can be diagnosed (empty results? wrong company/year? both?)
        source_summary = [f"{s['company']}/{s['fiscal_year']}" for s in result["sources"]]
        print(f"  \"{case['question'][:50]}\" -> {len(result['sources'])} sources: {source_summary}")

        hit = retrieval_hit(result["sources"], case["expected_company"], case["expected_fiscal_year"])
        coverage = keyword_coverage(result["answer"], case["expected_keywords"])
        results.append({**case, "retrieval_hit": hit, "keyword_coverage": coverage})

        time.sleep(2)  # avoid hammering the free-tier rate limit between calls
    return results


def _aggregate(results: list[dict]) -> dict:
    n = len(results)
    return {
        "hit_rate": sum(r["retrieval_hit"] for r in results) / n,
        "avg_coverage": sum(r["keyword_coverage"] for r in results) / n,
    }


def run():
    print("Running WITHOUT reranking (raw vector search order)...")
    without_rerank = _run_condition(use_reranking=False)

    print("Running WITH reranking...")
    with_rerank = _run_condition(use_reranking=True)

    stats_without = _aggregate(without_rerank)
    stats_with = _aggregate(with_rerank)

    print("\n" + "=" * 55)
    print("RERANKING A/B TEST RESULTS")
    print("=" * 55)
    print(f"{'Metric':<25}{'Without rerank':>15}{'With rerank':>15}")
    print(
        f"{'Retrieval hit rate':<25}{stats_without['hit_rate']:>14.0%} {stats_with['hit_rate']:>14.0%}"
    )
    print(
        f"{'Avg keyword coverage':<25}{stats_without['avg_coverage']:>14.0%} {stats_with['avg_coverage']:>14.0%}"
    )

    hit_delta = stats_with["hit_rate"] - stats_without["hit_rate"]
    coverage_delta = stats_with["avg_coverage"] - stats_without["avg_coverage"]
    print(f"\nHit rate change:      {hit_delta:+.0%}")
    print(f"Coverage change:      {coverage_delta:+.0%}")

    # Per-question breakdown — useful for spotting WHICH questions
    # reranking actually helped or hurt, not just the aggregate.
    print("\nPer-question breakdown:")
    for w, r in zip(without_rerank, with_rerank):
        marker = "improved" if r["keyword_coverage"] > w["keyword_coverage"] else (
            "worse" if r["keyword_coverage"] < w["keyword_coverage"] else "unchanged"
        )
        print(f"  [{marker:9}] {w['question'][:60]}")

    return {"without_rerank": stats_without, "with_rerank": stats_with}


if __name__ == "__main__":
    run()