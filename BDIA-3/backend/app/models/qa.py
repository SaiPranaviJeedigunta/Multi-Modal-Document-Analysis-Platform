from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class QuestionRequest(BaseModel):
    document_id: str
    question: str
    context: Optional[str] = None

class Answer(BaseModel):
    answer: str
    confidence_score: float
    source_references: List[str]
    generated_at: datetime

class ResearchNote(BaseModel):
    id: str
    document_id: str
    question: str
    answer: str
    verified: bool = False
    created_at: datetime
    verified_at: Optional[datetime] = None