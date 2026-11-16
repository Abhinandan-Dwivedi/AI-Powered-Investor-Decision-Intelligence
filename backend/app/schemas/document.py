from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    fiscal_year: int
    source_file: str
    content_hash: str
    status: str
    created_at: datetime
