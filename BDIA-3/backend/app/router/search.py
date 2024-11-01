from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from datetime import datetime
from ..models.search import (
    SearchRequest, 
    SearchResponse, 
    SearchResult, 
    SearchType
)
from ..services.search_service import SearchService
from ..services.auth_service import AuthService

router = APIRouter()

@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    current_user = Depends(AuthService.get_current_user),
    search_service: SearchService = Depends()
):
    """Perform hybrid search across documents and research notes"""
    try:
        return await search_service.hybrid_search(
            query=request.query,
            document_id=request.document_id,
            search_type=request.search_type,
            page=request.page,
            page_size=request.page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-notes/{note_id}", response_model=List[SearchResult])
async def find_similar_notes(
    note_id: str,
    limit: int = 5,
    current_user = Depends(AuthService.get_current_user),
    search_service: SearchService = Depends()
):
    """Find similar research notes"""
    try:
        return await search_service.search_similar_notes(
            note_id=note_id,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/time-range", response_model=SearchResponse)
async def search_by_time_range(
    query: str,
    start_date: datetime,
    end_date: datetime,
    search_type: SearchType = SearchType.BOTH,
    page: int = 1,
    page_size: int = 10,
    current_user = Depends(AuthService.get_current_user),
    search_service: SearchService = Depends()
):
    """Search within a specific time range"""
    try:
        return await search_service.search_by_time_range(
            query=query,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))