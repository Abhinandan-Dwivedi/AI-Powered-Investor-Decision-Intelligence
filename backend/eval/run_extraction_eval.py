"""
Compares stored FinancialMetric rows against hand-verified ground
truth, reporting field-level extraction accuracy.

Run from the backend/ directory (needs a live DB with already-ingested
documents matching the companies/years in golden_kpis.py):

    python -m eval.run_extraction_eval
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.golden_kpis import GOLDEN_KPIS, KPI_FIELDS
from eval.metrics import extraction_accuracy
from app.models.financial_metrics import FinancialMetric
from app.services.db import SessionLocal


def run():
    db = SessionLocal()
    results = []

    try:
        for case in GOLDEN_KPIS:
            row = (
                db.query(FinancialMetric)
                .filter(
                    FinancialMetric.company == case["company"],
                    FinancialMetric.fiscal_year == case["fiscal_year"],
                )
                .order_by(FinancialMetric.created_at.desc())
                .first()
            )

            print(f"\n> {case['company']} FY{case['fiscal_year']}")
            if row is None:
                print("  ERROR: no extracted metrics found — was this document ingested?")
                results.append({**case, "accuracy": 0.0, "mismatches": [{"field": "ALL", "reason": "not found"}]})
                continue

            extracted = {field: getattr(row, field) for field in KPI_FIELDS}
            result = extraction_accuracy(extracted, case["expected"], KPI_FIELDS)

            print(f"  accuracy={result['accuracy']:.0%}")
            for m in result["mismatches"]:
                print(f"    mismatch [{m['field']}]: extracted={m['extracted']!r} expected={m['expected']!r}")

            results.append({**case, **result})
    finally:
        db.close()

    _print_summary(results)
    return results


def _print_summary(results: list[dict]):
    n = len(results)
    if n == 0:
        print("No golden KPI cases defined yet — add entries to eval/golden_kpis.py")
        return

    avg_accuracy = sum(r["accuracy"] for r in results) / n

    print("\n" + "=" * 50)
    print("KPI EXTRACTION EVAL SUMMARY")
    print("=" * 50)
    print(f"Documents evaluated:  {n}")
    print(f"Avg field accuracy:   {avg_accuracy:.0%}")


if __name__ == "__main__":
    run()