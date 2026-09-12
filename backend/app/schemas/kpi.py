"""
Structured KPI extraction schema.

Design note (fixing a real bug found in the reference project): the
LLM is asked to return growth_drivers/risk_factors as JSON arrays, but
LLMs occasionally return a single string instead of a list — especially
when there's only one point to make. The reference repo's save logic
assumed a list and called .join() directly, which broke silently or
crashed depending on the value. Here, a field_validator normalizes
str -> [str] before the value ever reaches the database, so downstream
code can always safely assume a list.
"""
from pydantic import BaseModel, field_validator


class FinancialMetrics(BaseModel):
    company: str
    fiscal_year: int

    revenue: str | None = None
    net_income: str | None = None
    operating_income: str | None = None
    operating_cash_flow: str | None = None
    total_assets: str | None = None
    total_liabilities: str | None = None

    growth_drivers: list[str] = []
    risk_factors: list[str] = []

    @field_validator("growth_drivers", "risk_factors", mode="before")
    @classmethod
    def normalize_to_list(cls, value):
        """Coerce a stray string (or None) into a list, so callers never
        have to special-case the type themselves."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        return value

    @field_validator(
        "revenue",
        "net_income",
        "operating_income",
        "operating_cash_flow",
        "total_assets",
        "total_liabilities",
        mode="before",
    )
    @classmethod
    def blank_string_to_none(cls, value):
        """LLMs sometimes return "" or "N/A" instead of omitting a field
        entirely. Treat those as "not found" rather than storing junk."""
        if isinstance(value, str) and value.strip().lower() in ("", "n/a", "none", "unknown"):
            return None
        return value