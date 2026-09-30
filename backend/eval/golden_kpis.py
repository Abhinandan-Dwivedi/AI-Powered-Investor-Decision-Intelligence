"""
Ground-truth KPI values, taken directly from the actual filing (not
from our own extraction pipeline — that would be circular). Used to
measure how accurately extract_kpis() pulls real numbers out of a
document.

Source these from the real 10-K/annual report itself when you fill
this in, not from any AI-generated summary.
"""

GOLDEN_KPIS = [
    {
        "company": "Apple",
        "fiscal_year": 2024,
        "expected": {
            "revenue": "$391,035 million",
            "net_income": "$93,736 million",
            "operating_income": "$123,216 million",
            "operating_cash_flow": "$118,254 million",
            "total_assets": "$364,980 million",
            "total_liabilities": "$308,030 million",
        },
    },
    # Add one entry per ingested filing you want to evaluate extraction
    # accuracy against.
]

KPI_FIELDS = [
    "revenue",
    "net_income",
    "operating_income",
    "operating_cash_flow",
    "total_assets",
    "total_liabilities",
]