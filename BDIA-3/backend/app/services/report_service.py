from typing import Dict, List
from datetime import datetime
from ..models.document import Document
from ..services.nemo_multimodal_service import NeMoMultimodalService

class ReportService:
    def __init__(self, nemo_service: NeMoMultimodalService):
        self.nemo_service = nemo_service

    async def generate_report(
        self,
        document: Document,
        qa_interactions: List[Dict],
        include_visuals: bool = True
    ) -> Dict:
        """Generate a formatted report with links to visuals"""
        try:
            # Extract visual elements
            visual_elements = []
            if include_visuals:
                if document.image_link:
                    visual_content = await self.nemo_service.process_image(document.image_link)
                    visual_elements.append(visual_content)
                elif document.pdf_link:
                    visual_content = await self.nemo_service.process_pdf(document.pdf_link)
                    visual_elements.extend(visual_content)

            # Generate report content
            report_sections = []
            
            # Add summary section
            summary = await self.nemo_service.generate_visual_summary(document)
            report_sections.append({
                "type": "summary",
                "content": summary["summary"]
            })

            # Process Q&A interactions
            for qa in qa_interactions:
                response = await self.nemo_service.query_document(
                    query=qa["question"],
                    document=document,
                    visual_content=visual_elements[0] if visual_elements else None
                )
                
                report_sections.append({
                    "type": "qa",
                    "question": qa["question"],
                    "answer": response["answer"],
                    "references": response["references"]
                })

            # Format report with links
            formatted_report = self._format_report(report_sections, visual_elements)
            
            return formatted_report

        except Exception as e:
            raise Exception(f"Error generating report: {str(e)}")

    def _format_report(self, sections: List[Dict], visual_elements: List[Dict]) -> Dict:
        """Format report with proper structure and links"""
        return {
            "title": "Research Report",
            "generated_at": datetime.now(),
            "sections": sections,
            "visual_references": [
                {
                    "type": v["type"],
                    "reference": f"visual_{idx}",
                    "path": v["path"],
                    "page": v.get("page")
                }
                for idx, v in enumerate(visual_elements)
            ]
        }