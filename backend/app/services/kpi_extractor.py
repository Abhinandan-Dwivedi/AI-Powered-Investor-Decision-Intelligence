"""
KPI extraction: after a document is ingested, pull its own chunks back
out of Qdrant (filtered by company + fiscal_year + content_hash) and
ask the LLM to extract structured financial metrics + qualitative
insights from them.

Why filter by content_hash specifically: if the same company/year has
multiple filings (e.g., an amended 10-K), we want extraction to run
against exactly the document that was just ingested, not blend chunks
from a different filing of the same company/year together.
"""
import json
import re

from app.core.config import settings
from app.schemas.kpi import FinancialMetrics
from app.services.llm_generation import generate_answer
from app.services.vector_store import get_qdrant_client
from qdrant_client.models import Filter, FieldCondition, MatchValue

EXTRACTION_SYSTEM_PROMPT = """You are a financial data extraction engine. \
Given excerpts from a company's annual report, extract the following as \
strict JSON matching this exact shape:

{
  "revenue": "<total revenue with currency/unit, or null if not found>",
  "net_income": "<net income with currency/unit, or null if not found>",
  "operating_income": "<operating income with currency/unit, or null if not found>",
  "operating_cash_flow": "<operating cash flow with currency/unit, or null if not found>",
  "total_assets": "<total assets with currency/unit, or null if not found>",
  "total_liabilities": "<total liabilities with currency/unit, or null if not found>",
  "growth_drivers": ["<short bullet point>", "..."],
  "risk_factors": ["<short bullet point>", "..."]
}

Rules:
- Use null (not "N/A" or empty string) for any KPI you cannot find in the excerpts.
- growth_drivers and risk_factors MUST always be JSON arrays, even if you only find one point.
- Extract 3-5 growth_drivers and 3-5 risk_factors if the excerpts support it.
- Do not invent numbers. Only extract what is explicitly stated in the excerpts.
- Respond with ONLY the JSON object, no markdown fences, no commentary.
"""


def _fetch_document_chunks(company: str, fiscal_year: int, content_hash: str, limit: int = 60) -> list[str]:
    """Pull back all chunks belonging to this specific ingested document,
    using Qdrant's scroll API (not vector search — we want everything,
    not a similarity-ranked subset, since extraction needs broad coverage)."""
    client = get_qdrant_client()

    points, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="company", match=MatchValue(value=company)),
                FieldCondition(key="fiscal_year", match=MatchValue(value=fiscal_year)),
                FieldCondition(key="content_hash", match=MatchValue(value=content_hash)),
            ]
        ),
        limit=limit,
        with_payload=True,
    )
    # Preserve original document order using chunk_index, so the LLM reads
    # the report roughly front-to-back rather than in arbitrary order.
    points.sort(key=lambda p: p.payload.get("chunk_index", 0))
    return [p.payload["text"] for p in points]


def extract_kpis(company: str, fiscal_year: int, content_hash: str) -> FinancialMetrics:
    chunks = _fetch_document_chunks(company, fiscal_year, content_hash)

    if not chunks:
        raise ValueError(
            f"No chunks found for {company} FY{fiscal_year} (hash={content_hash[:12]}...) — "
            "was ingestion completed before calling extraction?"
        )

    document_text = "\n\n".join(chunks)
    user_prompt = f"Company: {company}\nFiscal Year: {fiscal_year}\n\nReport excerpts:\n{document_text}"

    raw_response = generate_answer(
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.extraction_model,
    )

    extracted_json = _extract_json_object(raw_response)
    extracted_json["company"] = company
    extracted_json["fiscal_year"] = fiscal_year

    # Pydantic validation happens here — this is where the string-vs-list
    # normalization and blank-string cleanup from kpi.py actually run.
    return FinancialMetrics(**extracted_json)


def _extract_json_object(raw_text: str) -> dict:
    """Extract a JSON object from the LLM's response, tolerating markdown
    code fences or stray text the model sometimes adds despite instructions."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in extraction output: {raw_text[:200]!r}")
    return json.loads(match.group(0))