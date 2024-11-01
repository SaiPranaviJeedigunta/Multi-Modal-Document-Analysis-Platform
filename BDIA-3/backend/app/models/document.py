from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Document(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    image_link: str
    pdf_link: str
    created_at: datetime
    updated_at: datetime

class DocumentSummary(BaseModel):
    document_id: str
    summary: str
    generated_at: datetime

class DocumentResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str]
    image_authenticated_url: str
    pdf_authenticated_url: str
    pdf_gcs_path: str