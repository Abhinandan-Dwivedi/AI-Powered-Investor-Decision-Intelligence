"""
Golden evaluation set for the RAG chat pipeline.

Each entry is a question with a known-correct expected source document
and a small set of keywords/facts that MUST appear in a correct
answer. This is intentionally small and hand-curated rather than
auto-generated — a golden set only has value if you trust every entry
is actually correct, which requires a human to have checked it against
the source filing.

Fill in real values matching whatever filings you've actually
ingested (company names, fiscal years) before running the eval script.
"""

GOLDEN_QUESTIONS = [
    {
        "question": "What was Apple's total revenue in fiscal year 2024?",
        "expected_company": "Apple",
        "expected_fiscal_year": 2024,
        "expected_keywords": ["391,035", "revenue"],
    },
    {
        "question": "What was Apple's net income for fiscal year 2024?",
        "expected_company": "Apple",
        "expected_fiscal_year": 2024,
        "expected_keywords": ["93,736", "net income"],
    },
    {
        "question": "What foreign exchange risks does Apple mention in its 2024 report?",
        "expected_company": "Apple",
        "expected_fiscal_year": 2024,
        "expected_keywords": ["dollar", "exchange"],
    },
    {
        "question": "What drove Apple's Services growth in fiscal year 2024?",
        "expected_company": "Apple",
        "expected_fiscal_year": 2024,
        "expected_keywords": ["services", "13%"],
    },
    # Add more questions here as you ingest more filings — each new
    # company/year you add should get at least 2-3 golden questions
    # covering both a hard number and a qualitative fact.
]