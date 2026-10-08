"""Compare no reranking vs LLM reranker vs cross-encoder on the golden set.

    python -m eval.run_reranker_comparison
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.golden_dataset import GOLDEN_QUESTIONS
from eval.metrics import keyword_coverage, retrieval_hit
from app.services.rag_chat_service import answer_question

BACKENDS = ["none", "llm", "cross_encoder"]


def run_backend(backend: str) -> dict:
    hits, coverages, latencies, errors = [], [], [], 0
    for case in GOLDEN_QUESTIONS:
        start = time.time()
        try:
            result = answer_question(case["question"], reranker=backend)
        except Exception as e:
            print(f"  [{backend}] ERROR on '{case['question'][:40]}': {e}")
            errors += 1
            continue
        latencies.append(time.time() - start)
        hits.append(retrieval_hit(result["sources"], case["expected_company"], case["expected_fiscal_year"]))
        coverages.append(keyword_coverage(result["answer"], case["expected_keywords"]))
        time.sleep(2)  # stay under the free-tier rate limit
    n = len(hits) or 1
    return {
        "hit_rate": sum(hits) / n,
        "coverage": sum(coverages) / n,
        "avg_seconds": sum(latencies) / n,
        "errors": errors,
    }


def run():
    results = {}
    for backend in BACKENDS:
        print(f"Running {backend}...")
        results[backend] = run_backend(backend)

    print(f"\n{'Backend':<16}{'Hit rate':>10}{'Coverage':>10}{'Avg sec':>10}{'Errors':>8}")
    for name, r in results.items():
        print(f"{name:<16}{r['hit_rate']:>9.0%}{r['coverage']:>10.0%}{r['avg_seconds']:>10.1f}{r['errors']:>8}")


if __name__ == "__main__":
    run()