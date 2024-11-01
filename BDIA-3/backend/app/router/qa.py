from fastapi import APIRouter, Depends, HTTPException
#from ..services.nemo_service import NeMoService
from ..services.nemo_multimodal_service import NeMoMultimodalService
from ..services.auth_service import AuthService
from ..services.snowflake_service import SnowflakeService
from ..services.research_notes_service import ResearchNotesService
from ..services.vector_store_service import VectorStoreService
from datetime import datetime

from ..models.qa import QuestionRequest, Answer

router = APIRouter()
#nemo_service = NeMoService()
nemo_service = NeMoMultimodalService()
vector_store_service=VectorStoreService()
notes_service=ResearchNotesService()
snowflake_service=SnowflakeService()


@router.post("/ask", response_model=Answer)
async def process_question(
    request: QuestionRequest,
    current_user = Depends(AuthService.get_current_user)
):
    """Process question using multi-modal RAG"""
    try:
        # Get document metadata and relevant chunks only
        document_chunks = await vector_store_service.get_relevant_chunks(
            document_id=request.document_id,
            query=request.question
        )
        
        # Process with NeMo
        response = await nemo_service.process_multimodal_query(
            query=request.question,
            context=document_chunks
        )
        
        # Generate research note
        research_note = await nemo_service.generate_research_note({
            "question": request.question,
            "answer": response.answer,
            "references": response.references
        })
        
        # Store for validation
        await notes_service.create_pending_note(
            document_id=request.document_id,
            content=research_note,
            metadata=response.metadata
        )
        
        return {
            "answer": response.answer,
            "confidence_score": response.confidence,
            "source_references": response.references,
            "generated_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal-query")
async def process_multimodal_query(
    document_id: str,
    query: str,
    include_visual: bool = True,
    current_user = Depends(AuthService.get_current_user)
):
    """Process a multimodal query against a document"""
    try:
        # Get document
        document = await snowflake_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Process visual content if requested
        visual_content = None
        if include_visual:
            if document.image_link:
                visual_content = await nemo_service.process_image(document.image_link)
            elif document.pdf_link:
                visual_content = await nemo_service.process_pdf(document.pdf_link)
        
        # Process query
        response = await nemo_service.query_document(
            query=query,
            document=document,
            visual_content=visual_content
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))