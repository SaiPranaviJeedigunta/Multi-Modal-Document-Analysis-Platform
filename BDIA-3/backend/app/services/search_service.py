from typing import List, Dict, Optional, Union
from datetime import datetime
from ..models.search import SearchType, SearchResult, SearchResponse, VisualReference
from .vector_store_service import VectorStoreService
from .nemo_multimodal_service import NeMoMultimodalService
from .research_notes_service import ResearchNotesService

class SearchService:
    def __init__(
        self,
        vector_store: VectorStoreService,
        nemo_service: NeMoMultimodalService,
        notes_service: ResearchNotesService
    ):
        self.vector_store = vector_store
        self.nemo_service = nemo_service
        self.notes_service = notes_service

    async def hybrid_search(
        self,
        query: str,
        document_id: Optional[str] = None,
        search_type: SearchType = SearchType.BOTH,
        page: int = 1,
        page_size: int = 10
    ) -> SearchResponse:
        """
        Perform hybrid search across documents and research notes
        """
        try:
            results: List[SearchResult] = []
            
            # Process query with NeMo for semantic understanding
            query_embedding = await self.nemo_service.process_query(query)
            
            if search_type in [SearchType.DOCUMENT, SearchType.BOTH]:
                # Search in documents
                doc_results = await self.vector_store.search_document(
                    document_id=document_id,
                    query=query,
                    query_embedding=query_embedding,
                    top_k=page_size
                )
                
                # Process document results
                for r in doc_results:
                    # Extract visual references from metadata
                    visual_refs = []
                    if r.metadata.get('visual_elements'):
                        visual_refs = [
                            VisualReference(
                                type=v['type'],
                                page=v['page'],
                                caption=v.get('caption', '')
                            )
                            for v in r.metadata['visual_elements']
                        ]
                    
                    results.append(
                        SearchResult(
                            document_id=document_id or r.metadata.get('document_id'),
                            content=r.text,
                            relevance_score=r.score,
                            source_type="document",
                            page_number=r.metadata.get("page_number"),
                            visual_references=visual_refs,
                            timestamp=r.metadata.get("timestamp", datetime.now())
                        )
                    )
            
            if search_type in [SearchType.RESEARCH_NOTES, SearchType.BOTH]:
                # Search in research notes
                note_results = await self.vector_store.search_research_notes(
                    document_id=document_id,
                    query=query,
                    query_embedding=query_embedding,
                    top_k=page_size
                )
                
                # Process research note results
                for r in note_results:
                    results.append(
                        SearchResult(
                            document_id=document_id or r.metadata.get('document_id'),
                            content=r.text,
                            relevance_score=r.score,
                            source_type="research_note",
                            page_number=None,
                            visual_references=[],
                            timestamp=r.metadata.get("timestamp", datetime.now()),
                            verified=r.metadata.get("verified", False),
                            validator=r.metadata.get("validator")
                        )
                    )
            
            # Sort results by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Calculate pagination
            total_results = len(results)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_results)
            paginated_results = results[start_idx:end_idx]
            
            return SearchResponse(
                results=paginated_results,
                total_results=total_results,
                page=page,
                total_pages=(total_results + page_size - 1) // page_size,
                query=query,
                search_type=search_type,
                document_id=document_id
            )
            
        except Exception as e:
            raise Exception(f"Error performing hybrid search: {str(e)}")

    async def search_similar_notes(
        self,
        note_id: str,
        limit: int = 5
    ) -> List[SearchResult]:
        """Find similar research notes"""
        try:
            # Get original note
            note = await self.notes_service.get_note(note_id)
            if not note:
                raise Exception(f"Research note {note_id} not found")
            
            # Get note embedding
            note_embedding = await self.nemo_service.get_embedding(note.content)
            
            # Search for similar notes
            similar_notes = await self.vector_store.search_research_notes(
                query_embedding=note_embedding,
                exclude_ids=[note_id],
                top_k=limit
            )
            
            return [
                SearchResult(
                    document_id=r.metadata.get('document_id'),
                    content=r.text,
                    relevance_score=r.score,
                    source_type="research_note",
                    timestamp=r.metadata.get("timestamp", datetime.now()),
                    verified=r.metadata.get("verified", False),
                    validator=r.metadata.get("validator")
                ) for r in similar_notes
            ]
            
        except Exception as e:
            raise Exception(f"Error finding similar notes: {str(e)}")

    async def search_by_time_range(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        search_type: SearchType = SearchType.BOTH,
        page: int = 1,
        page_size: int = 10
    ) -> SearchResponse:
        """Search within a specific time range"""
        try:
            # Perform base search
            search_response = await self.hybrid_search(
                query=query,
                search_type=search_type,
                page=1,  # Get all results for filtering
                page_size=1000
            )
            
            # Filter by date range
            filtered_results = [
                r for r in search_response.results
                if start_date <= r.timestamp <= end_date
            ]
            
            # Paginate filtered results
            total_results = len(filtered_results)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_results)
            
            return SearchResponse(
                results=filtered_results[start_idx:end_idx],
                total_results=total_results,
                page=page,
                total_pages=(total_results + page_size - 1) // page_size,
                query=query,
                search_type=search_type
            )
            
        except Exception as e:
            raise Exception(f"Error performing time range search: {str(e)}")