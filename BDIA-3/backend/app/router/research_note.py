from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from ..models.research_note import ResearchNote, ResearchNoteCreate
from ..services.vector_store_service import VectorStoreService
from ..services.auth_service import AuthService

router = APIRouter()
vector_store = VectorStoreService()

@router.post("/notes/{document_id}")
async def add_research_note(
    document_id: str,
    note: ResearchNoteCreate,
    current_user = Depends(AuthService.get_current_user)
):
    """Add a new research note to the document index"""
    try:
        timestamp = datetime.now()
        await vector_store.add_research_note(
            document_id=document_id,
            note=note.content,
            timestamp=timestamp
        )
        return {"status": "success", "timestamp": timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/{document_id}")
async def get_document_notes(
    document_id: str,
    current_user = Depends(AuthService.get_current_user)
):
    """Retrieve all research notes for a document"""
    return await vector_store.get_research_notes(document_id)

@router.post("/search")
async def search_content(
    query: str,
    document_id: Optional[str] = None,
    search_type: str = "hybrid",
    current_user = Depends(AuthService.get_current_user)
):
    """Search through documents and research notes"""
    try:
        if document_id:
            # Search within specific document
            results = await vector_store.search_document(
                document_id=document_id,
                query=query,
                search_type=search_type
            )
        else:
            # Hybrid search across all content
            results = await vector_store.hybrid_search(query)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))