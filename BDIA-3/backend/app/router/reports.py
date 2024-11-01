from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from ..models.document import Document
from ..services.report_generation_service import ReportGenerationService
from ..services.auth_service import AuthService
from datetime import datetime

router = APIRouter()
report_service = ReportGenerationService()

@router.post("/generate/{document_id}")
async def generate_document_report(
    document_id: str,
    question: str,
    answer: str,
    visual_elements: List[Dict],
    metadata: Dict = None,
    current_user = Depends(AuthService.get_current_user)
):
    """Generate a research report for a document"""
    try:
        # Get document from Snowflake
        document = await snowflake_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Add analyst info to metadata
        if metadata is None:
            metadata = {}
        metadata["analyst"] = current_user.username
        metadata["generated_at"] = datetime.now().isoformat()

        # Generate report
        report = await report_service.generate_research_report(
            document=document,
            question=question,
            answer=answer,
            visual_elements=visual_elements,
            metadata=metadata
        )

        # Save report
        report_path = f"/reports/{document_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        saved_path = await report_service.save_report(
            report=report,
            save_path=report_path
        )

        return {
            "status": "success",
            "report": report,
            "saved_path": saved_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))