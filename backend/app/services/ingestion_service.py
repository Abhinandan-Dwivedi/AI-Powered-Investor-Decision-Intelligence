import uuid
from pathlib import Path

from qdrant_client.models import PointStruct
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.financial_metrics import Document, FinancialMetric
from app.services.chunker import chunk_markdown
from app.services.embeddings import embed_texts
from app.services.kpi_extractor import extract_kpis
from app.services.pdf_processor import compute_content_hash, pdf_to_markdown
from app.services.retention import enforce_retention
from app.services.vector_store import upsert_chunks


class DuplicateDocumentError(Exception):
    """Raised when a file with the same content hash was already ingested."""

    def __init__(self, existing_document: Document):
        self.existing_document = existing_document
        super().__init__(
            f"Document already ingested as id={existing_document.id} "
            f"(company={existing_document.company}, year={existing_document.fiscal_year})"
        )


def _deterministic_point_id(content_hash: str, chunk_index: int) -> str:
    """Deterministic UUID per (document, chunk_index). Re-ingesting the
    same content produces the same point IDs, so Qdrant's upsert
    overwrites in place instead of creating new points."""
    namespace = uuid.UUID("12345678-1234-5678-1234-567812345678")
    return str(uuid.uuid5(namespace, f"{content_hash}:{chunk_index}"))


def ingest_document(
    db: Session,
    file_bytes: bytes,
    filename: str,
    company: str,
    fiscal_year: int,
) -> Document:
    """Full ingestion pipeline for one uploaded PDF.

    Steps: hash check -> save raw PDF -> convert to markdown -> chunk
    -> embed -> upsert to Qdrant -> record Document + chunk_count in
    Postgres.
    """
    content_hash = compute_content_hash(file_bytes)

    existing = db.query(Document).filter(Document.content_hash == content_hash).first()
    if existing:
        raise DuplicateDocumentError(existing)

    # Persist the raw PDF to disk for traceability / re-processing later.
    raw_dir = Path(settings.raw_pdf_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = raw_dir / f"{content_hash}_{filename}"
    pdf_path.write_bytes(file_bytes)

    # Create the Document row up front with status="processing" so partial
    # failures are visible in the DB rather than silently vanishing.
    document = Document(
        company=company,
        fiscal_year=fiscal_year,
        source_file=filename,
        content_hash=content_hash,
        chunk_count=0,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        markdown_text = pdf_to_markdown(pdf_path)
        chunks = chunk_markdown(markdown_text)

        if not chunks:
            document.status = "failed"
            db.commit()
            raise ValueError(f"No usable text extracted from '{filename}'.")

        vectors = embed_texts([c.text for c in chunks])

        points = [
            PointStruct(
                id=_deterministic_point_id(content_hash, chunk.chunk_index),
                vector=vector,
                payload={
                    "text": chunk.text,
                    "company": company,
                    "fiscal_year": fiscal_year,
                    "source_file": filename,
                    "content_hash": content_hash,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        upsert_chunks(points)

        document.chunk_count = len(chunks)
        document.status = "completed"
        db.commit()
        db.refresh(document)

        # The raw PDF is only needed for conversion. Chunks now live in
        # Qdrant (and KPI extraction reads from there), so keeping the
        # file just grows disk usage forever.
        _remove_raw_pdf(pdf_path)

        # KPI extraction runs after ingestion succeeds. It's treated as a
        # best-effort enhancement, not a hard requirement: if extraction
        # fails (e.g. LLM hiccup, unusual report format), the document is
        # still fully ingested and searchable via chat — we just won't have
        # dashboard KPI cards for it yet. This mirrors how the reranker
        # degrades gracefully rather than blocking the whole chat request.
        try:
            metrics = extract_kpis(
                company=company,
                fiscal_year=fiscal_year,
                content_hash=content_hash,
            )
            db.add(
                FinancialMetric(
                    document_id=document.id,
                    company=metrics.company,
                    fiscal_year=metrics.fiscal_year,
                    revenue=metrics.revenue,
                    net_income=metrics.net_income,
                    operating_income=metrics.operating_income,
                    operating_cash_flow=metrics.operating_cash_flow,
                    total_assets=metrics.total_assets,
                    total_liabilities=metrics.total_liabilities,
                    growth_drivers=metrics.growth_drivers,
                    risk_factors=metrics.risk_factors,
                )
            )
            db.commit()
        except Exception as extraction_error:
            # Log and move on — do not let a KPI extraction failure roll
            # back or fail the ingestion that already succeeded.
            print(f"[kpi_extraction] Failed for document {document.id}: {extraction_error}")

        # Retention runs only now — after the new document succeeded and
        # its KPIs were attempted — so we never evict old data in exchange
        # for an ingestion that didn't work. It's housekeeping: a failure
        # here must not turn a successful ingestion into an error.
        try:
            enforce_retention(db, keep_document_id=document.id)
        except Exception as retention_error:
            db.rollback()
            print(f"[retention] Failed after ingesting document {document.id}: {retention_error}")

        return document

    except Exception:
        document.status = "failed"
        db.commit()
        # Failed uploads would otherwise leak their PDF on disk forever.
        _remove_raw_pdf(pdf_path)
        raise


def _remove_raw_pdf(pdf_path: Path) -> None:
    """Best-effort delete of the raw PDF. A failed unlink only logs —
    it must never change the outcome of the ingestion."""
    try:
        pdf_path.unlink(missing_ok=True)
    except Exception as unlink_error:
        print(f"[ingestion] Could not delete raw PDF '{pdf_path}': {unlink_error}")