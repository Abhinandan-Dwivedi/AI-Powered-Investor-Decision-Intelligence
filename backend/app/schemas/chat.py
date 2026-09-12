from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    company: str | None = None       # optional filter, e.g. "Apple"
    fiscal_year: int | None = None   # optional filter, e.g. 2024


class SourceChunk(BaseModel):
    text: str
    company: str
    fiscal_year: int
    source_file: str
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]