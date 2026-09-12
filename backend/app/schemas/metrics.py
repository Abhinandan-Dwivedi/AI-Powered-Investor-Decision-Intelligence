from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FinancialMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    fiscal_year: int
    revenue: str | None
    net_income: str | None
    operating_income: str | None
    operating_cash_flow: str | None
    total_assets: str | None
    total_liabilities: str | None
    growth_drivers: list[str]
    risk_factors: list[str]
    created_at: datetime