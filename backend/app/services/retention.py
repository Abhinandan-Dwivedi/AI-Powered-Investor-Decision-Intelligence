from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.financial_metrics import Document, FinancialMetric
from app.services.vector_store import delete_by_content_hash


def enforce_retention(db: Session, keep_document_id: int | None = None) -> list[int]:
    """Evict completed documents beyond the newest `settings.max_documents`.

    Only "completed" documents count toward the cap — "processing" rows
    may be in-flight and "failed" rows hold no vectors worth capping.

    `keep_document_id` protects the document that was just ingested. It
    is normally the newest anyway, but `created_at` is stamped when
    processing *starts*, so a slow ingestion that overlaps a faster one
    could otherwise sort below the cap and be evicted the moment it
    finishes.

    Returns the ids of the evicted documents.
    """
    completed = (
        db.query(Document)
        .filter(Document.status == "completed")
       
        .order_by(Document.created_at.desc(), Document.id.desc())
        .all()
    )

    to_evict = [
        doc for doc in completed[settings.max_documents:] if doc.id != keep_document_id
    ]

    raw_dir = Path(settings.raw_pdf_dir)
    evicted_ids: list[int] = []

    for doc in to_evict:
       
        doc_id, company, fiscal_year = doc.id, doc.company, doc.fiscal_year
        try:
            # 1. Vectors in Qdrant.
            delete_by_content_hash(doc.content_hash)
 
            if raw_dir.exists():
                for leftover in raw_dir.glob(f"{doc.content_hash}_*"):
                    leftover.unlink(missing_ok=True)
 
            db.query(FinancialMetric).filter(
                FinancialMetric.document_id == doc_id
            ).delete(synchronize_session=False)

          
            db.delete(doc)
 
            db.commit()
            evicted_ids.append(doc_id)
            print(
                f"[retention] Evicted document id={doc_id} "
                f"(company={company}, fiscal_year={fiscal_year})"
            )
        except Exception as eviction_error:
       
            db.rollback()
            print(f"[retention] Failed to evict document id={doc_id}: {eviction_error}")

    if evicted_ids:
        print(
            f"[retention] Evicted {len(evicted_ids)} document(s); "
            f"cap is {settings.max_documents} completed documents."
        )

    return evicted_ids
