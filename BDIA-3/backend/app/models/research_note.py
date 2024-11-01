from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ResearchNoteCreate(BaseModel):
    content: str
    source_type: str = "manual"  # manual, qa_derived, summary_derived

class ResearchNote(BaseModel):
    id: str
    document_id: str
    content: str
    created_at: datetime
    source_type: str
    metadata: Optional[dict] = None