"""
Pure scoring functions for the evaluation harness. No network calls,
no DB — these just compare structured inputs and produce numbers, so
they can be unit tested in isolation from the LLM/retrieval pipeline
they're meant to evaluate.
"""


def retrieval_hit(sources: list[dict], expected_company: str, expected_fiscal_year: int) -> bool:
    """Did at least one retrieved source come from the expected document?
    This catches the most basic retrieval failure: answering a question
    about Apple using a chunk that was actually retrieved from a
    different company or year."""
    return any(
        s["company"] == expected_company and s["fiscal_year"] == expected_fiscal_year
        for s in sources
    )


def keyword_coverage(answer: str, expected_keywords: list[str]) -> float:
    """Fraction of expected keywords/facts that appear in the answer text
    (case-insensitive substring match). This is a coarse proxy for
    groundedness — not a substitute for human review, but cheap enough
    to run on every eval question and catches obvious omissions (e.g.
    the model answered evasively without stating the actual figure)."""
    if not expected_keywords:
        return 1.0

    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return hits / len(expected_keywords)


def field_match(extracted_value: str | None, expected_value: str | None) -> bool:
    """Compare one extracted KPI field against a known-correct value.

    Financial figures vary in formatting without being wrong — currency
    symbols, commas, and unit abbreviations ("$391,035M" vs "391,035
    million" vs "391035.0") are all the same fact. We normalize both
    before comparing rather than requiring an exact string match, which
    would flag every harmless formatting difference as an extraction
    error.
    """
    if extracted_value is None and expected_value is None:
        return True
    if extracted_value is None or expected_value is None:
        return False

    return _normalize_financial_string(extracted_value) == _normalize_financial_string(expected_value)


_UNIT_EXPANSIONS = {
    "b": "billion",
    "bn": "billion",
    "m": "million",
    "mn": "million",
    "k": "thousand",
}


def _normalize_financial_string(value: str) -> str:
    """Lowercase, strip currency symbols/commas/whitespace, and expand
    common unit abbreviations so "$391,035M" and "391035 million"
    compare equal."""
    text = value.lower().strip()
    text = "".join(ch for ch in text if ch.isalnum() or ch.isspace())
    tokens = text.split()

    # Expand a trailing unit abbreviation glued to the number (e.g. "391035m")
    # or given as a separate token (e.g. "391035 m").
    expanded_tokens = []
    for token in tokens:
        for abbr, full in _UNIT_EXPANSIONS.items():
            if token == abbr:
                token = full
                break
            if token.endswith(abbr) and token[: -len(abbr)].replace(".", "").isdigit():
                token = token[: -len(abbr)] + full
                break
        expanded_tokens.append(token)

    return "".join(expanded_tokens)


def extraction_accuracy(extracted: dict, expected: dict, fields: list[str]) -> dict:
    """Field-by-field comparison. Returns {"accuracy": float, "mismatches": [...]}."""
    mismatches = []
    for field in fields:
        if not field_match(extracted.get(field), expected.get(field)):
            mismatches.append(
                {"field": field, "extracted": extracted.get(field), "expected": expected.get(field)}
            )

    accuracy = (len(fields) - len(mismatches)) / len(fields) if fields else 1.0
    return {"accuracy": accuracy, "mismatches": mismatches}