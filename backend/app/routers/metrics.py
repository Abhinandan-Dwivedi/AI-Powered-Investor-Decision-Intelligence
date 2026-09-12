from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.financial_metrics import FinancialMetric
from app.schemas.metrics import FinancialMetricResponse
from app.services.db import get_db

router = APIRouter()


@router.get("/metrics", response_model=list[FinancialMetricResponse])
def list_metrics(
    company: str | None = Query(default=None),
    fiscal_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Fetch extracted KPIs, optionally filtered by company/year.
    Powers the dashboard's KPI cards (Step 5)."""
    query = db.query(FinancialMetric)
    if company:
        query = query.filter(FinancialMetric.company == company)
    if fiscal_year:
        query = query.filter(FinancialMetric.fiscal_year == fiscal_year)

    # Latest extraction per row first — if a document is ever re-ingested
    # and re-extracted, the newest result should surface first.
    return query.order_by(FinancialMetric.created_at.desc()).all()