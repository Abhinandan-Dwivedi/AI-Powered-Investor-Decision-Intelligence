"""
Core tables.

Design notes vs. the reference project:
- risk_factors / growth_drivers are JSONB arrays, not newline-joined
  strings. That earlier approach caused stray text (even an HTML
  snippet) to leak into the data. JSONB lets the frontend render each
  bullet directly without string parsing.
- `documents` tracks every ingested file by content hash, so the same
  PDF uploaded twice is detected and skipped instead of silently
  duplicating chunks in the vector store.
"""
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Document(Base):
    """One row per ingested source file (PDF)."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_documents_content_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(120), index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, index=True)
    source_file: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)  # sha256 hex digest
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing|completed|failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    metrics: Mapped[list["FinancialMetric"]] = relationship(back_populates="document")


class FinancialMetric(Base):
    """Extracted KPIs + qualitative insights for one company/fiscal year."""

    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))

    company: Mapped[str] = mapped_column(String(120), index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, index=True)

    revenue: Mapped[str | None] = mapped_column(String(50), nullable=True)
    net_income: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operating_income: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operating_cash_flow: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_assets: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_liabilities: Mapped[str | None] = mapped_column(String(50), nullable=True)

    growth_drivers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    risk_factors: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="metrics")
