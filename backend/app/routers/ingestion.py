from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.ingestion import IngestionResponse
from app.services.db import get_db
from app.services.ingestion_service import DuplicateDocumentError, ingest_document

router = APIRouter()


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_report(
    file: UploadFile = File(...),
    company: str = Form(...),
    fiscal_year: int = Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds max size of {settings.max_upload_size_mb} MB.",
        )

    try:
        document = ingest_document(
            db=db,
            file_bytes=file_bytes,
            filename=file.filename,
            company=company,
            fiscal_year=fiscal_year,
        )
    except DuplicateDocumentError as e:
        # Not a failure — tell the client this exact file is already indexed.
        existing = e.existing_document
        return IngestionResponse(
            document_id=existing.id,
            company=existing.company,
            fiscal_year=existing.fiscal_year,
            status="duplicate",
            chunk_count=existing.chunk_count,
            message="This exact file was already ingested; skipped re-processing.",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return IngestionResponse(
        document_id=document.id,
        company=document.company,
        fiscal_year=document.fiscal_year,
        status=document.status,
        chunk_count=document.chunk_count,
        message="Document ingested successfully.",
    )
