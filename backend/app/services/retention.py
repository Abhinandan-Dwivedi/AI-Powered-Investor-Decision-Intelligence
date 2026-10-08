"""
Retention policy: keep only the newest `settings.max_documents`
completed documents.

Without this, every upload adds vectors to Qdrant and rows to Postgres
forever. After each successful ingestion we evict the oldest completed
documents beyond the cap.

Deletion order per document is deliberate: external stores first
(Qdrant vectors, leftover PDF files), Postgres last. If anything fails
midway, the Document row still exists, so the next run finds it again
and retries the cleanup. Deleting the Postgres row first would leave
orphaned vectors that nothing points to and nothing will ever clean up.
"""
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
        # id as a tiebreaker keeps the ordering stable if two rows share
        # the same created_at timestamp.
        .order_by(Document.created_at.desc(), Document.id.desc())
        .all()
    )

    to_evict = [
        doc for doc in completed[settings.max_documents:] if doc.id != keep_document_id
    ]

    raw_dir = Path(settings.raw_pdf_dir)
    evicted_ids: list[int] = []

    for doc in to_evict:
        # Capture identifying fields up front: after delete + commit the
        # ORM instance is expired and attribute access would fail.
        doc_id, company, fiscal_year = doc.id, doc.company, doc.fiscal_year
        try:
            # 1. Vectors in Qdrant.
            delete_by_content_hash(doc.content_hash)

            # 2. Any raw PDF left behind (e.g. ingested before PDFs were
            #    deleted on success, or a failed unlink).
            if raw_dir.exists():
                for leftover in raw_dir.glob(f"{doc.content_hash}_*"):
                    leftover.unlink(missing_ok=True)

            # 3. KPI rows — must go before the Document row because of the
            #    financial_metrics.document_id foreign key.
            db.query(FinancialMetric).filter(
                FinancialMetric.document_id == doc_id
            ).delete(synchronize_session=False)

            # 4. The Document row itself.
            db.delete(doc)

            # Commit per document so one bad eviction doesn't undo the
            # ones that already succeeded.
            db.commit()
            evicted_ids.append(doc_id)
            print(
                f"[retention] Evicted document id={doc_id} "
                f"(company={company}, fiscal_year={fiscal_year})"
            )
        except Exception as eviction_error:
            # Roll back so the session is usable for the next document;
            # the Document row survives and the next run will retry.
            db.rollback()
            print(f"[retention] Failed to evict document id={doc_id}: {eviction_error}")

    if evicted_ids:
        print(
            f"[retention] Evicted {len(evicted_ids)} document(s); "
            f"cap is {settings.max_documents} completed documents."
        )

    return evicted_ids
