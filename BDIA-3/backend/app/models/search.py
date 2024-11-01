from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class SearchType(str, Enum):
    DOCUMENT = "document"
    RESEARCH_NOTES = "research_notes"
    BOTH = "both"

class VisualReference(BaseModel):
    type: str
    page: int
    caption: Optional[str] = None

class SearchResult(BaseModel):
    document_id: str
    content: str
    relevance_score: float
    source_type: str
    page_number: Optional[int] = None
    visual_references: List[VisualReference] = []
    timestamp: datetime
    verified: Optional[bool] = None
    validator: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    search_type: SearchType = SearchType.BOTH
    page: int = 1
    page_size: int = 10

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int
    page: int
    total_pages: int
    query: str
    search_type: SearchType
    document_id: Optional[str] = None