from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
from ..models.document import Document, DocumentSummary
from ..services.snowflake_service import SnowflakeService
from ..services.summarization_service import SummarizationService
from ..services.auth_service import AuthService
from ..services.nemo_multimodal_service import NeMoMultimodalService

router = APIRouter()
snowflake_service = SnowflakeService()
summarization_service = SummarizationService()
nemo_service = NeMoMultimodalService()



@router.post("/{document_id}/summary", response_model=DocumentSummary)
async def generate_document_summary(
    document_id: str,
    current_user = Depends(AuthService.get_current_user)
):
    """Generate a summary for a specific document"""
    try:
        # Get document from Snowflake
        document = await snowflake_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Generate summary
        summary_result = await summarization_service.generate_document_summary(
            pdf_path=document.pdf_link
        )

        # Store summary in database
        await snowflake_service.update_document_summary(
            document_id=document_id,
            summary=summary_result["summary"]
        )

        return {
            "document_id": document_id,
            "summary": summary_result["summary"],
            "metadata": summary_result["metadata"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/research-summary")
async def generate_research_summary(
    document_id: str,
    current_user = Depends(AuthService.get_current_user)
):
    """Generate a research summary from Q&A interactions"""
    try:
        # Get Q&A interactions for the document
        qa_interactions = await snowflake_service.get_document_qa_interactions(document_id)
        
        # Generate research note summary
        research_summary = await summarization_service.generate_research_note_summary(
            qa_interactions=qa_interactions
        )

        # Store research summary
        await snowflake_service.store_research_summary(
            document_id=document_id,
            summary=research_summary
        )

        return {"research_summary": research_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{document_id}/multimodal-summary")
async def generate_multimodal_summary(
    document_id: str,
    current_user = Depends(AuthService.get_current_user)
):
    """Generate a multimodal summary incorporating visual elements"""
    try:
        # Get document
        document = await snowflake_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Generate multimodal summary
        summary_result = await nemo_service.generate_visual_summary(document)
        
        # Store summary
        await snowflake_service.update_document_summary(
            document_id=document_id,
            summary=summary_result["summary"]
        )
        
        return summary_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))