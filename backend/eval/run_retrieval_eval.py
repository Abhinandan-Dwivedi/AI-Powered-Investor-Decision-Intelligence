"""
Runs the golden question set through the real RAG chat pipeline and
reports two numbers per question:

  - retrieval hit:     did we pull context from the right document?
  - keyword coverage:  does the generated answer actually contain the
                        expected facts?

Run from the backend/ directory (needs the app importable + live
Postgres/Qdrant/LLM key configured):

    python -m eval.run_retrieval_eval
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.golden_dataset import GOLDEN_QUESTIONS
from eval.metrics import keyword_coverage, retrieval_hit
from app.services.rag_chat_service import answer_question


def run():
    results = []

    for case in GOLDEN_QUESTIONS:
        print(f"\n> {case['question']}")
        try:
            result = answer_question(case["question"])
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({**case, "retrieval_hit": False, "keyword_coverage": 0.0, "error": str(e)})
            continue

        hit = retrieval_hit(result["sources"], case["expected_company"], case["expected_fiscal_year"])
        coverage = keyword_coverage(result["answer"], case["expected_keywords"])

        print(f"  retrieval_hit={hit}  keyword_coverage={coverage:.0%}")
        print(f"  answer: {result['answer'][:150]}...")

        results.append({**case, "retrieval_hit": hit, "keyword_coverage": coverage})

    _print_summary(results)
    return results


def _print_summary(results: list[dict]):
    n = len(results)
    hit_rate = sum(r["retrieval_hit"] for r in results) / n
    avg_coverage = sum(r["keyword_coverage"] for r in results) / n
    failures = [r for r in results if not r["retrieval_hit"] or r["keyword_coverage"] < 1.0]

    print("\n" + "=" * 50)
    print("RETRIEVAL + ANSWER EVAL SUMMARY")
    print("=" * 50)
    print(f"Questions evaluated:   {n}")
    print(f"Retrieval hit rate:    {hit_rate:.0%}")
    print(f"Avg keyword coverage:  {avg_coverage:.0%}")

    if failures:
        print(f"\n{len(failures)} question(s) with issues:")
        for f in failures:
            print(f"  - \"{f['question']}\" (hit={f['retrieval_hit']}, coverage={f['keyword_coverage']:.0%})")
    else:
        print("\nAll questions passed both checks.")


if __name__ == "__main__":
    run()