from pydantic import BaseModel, Field


class IngestionResponse(BaseModel):
    document_id: int
    company: str
    fiscal_year: int
    status: str
    chunk_count: int
    message: str


class IngestionStatus(BaseModel):
    document_id: int
    company: str
    fiscal_year: int
    status: str
    chunk_count: int
    source_file: str
