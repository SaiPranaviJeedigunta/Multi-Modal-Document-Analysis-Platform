from typing import List, Dict, Optional
from datetime import datetime
import nemo.collections.nlp as nemo_nlp
from ..models.document import Document
from ..config.nemo_config import NeMoConfig

class ReportGenerationService:
    def __init__(self):
        self.config = NeMoConfig()
        # Initialize NeMo model for report generation
        self.report_model = nemo_nlp.models.TextModel.from_pretrained(
            "nvidia/nemo-megatron-gpt-1.3B"  # Using a more specific model
        )
        
    async def generate_research_report(
        self,
        document: Document,
        question: str,
        answer: str,
        visual_elements: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Generate formatted research report with visual references
        
        Args:
            document: Source document
            question: Research question
            answer: Generated answer
            visual_elements: List of visual elements (graphs, tables, etc.)
            metadata: Additional metadata for the report
            
        Returns:
            Dict containing formatted report with references
        """
        try:
            # Format visual elements with proper references
            visual_references = []
            page_references = {}
            
            for elem in visual_elements:
                ref_id = f"{elem['type']}_{elem['id']}"
                page_num = elem.get('page_number', 'N/A')
                
                if elem["type"] == "graph":
                    caption = f"Graph {elem['id']}: {elem['caption']}"
                    visual_references.append({
                        "ref_id": ref_id,
                        "type": "graph",
                        "caption": caption,
                        "page": page_num,
                        "path": elem.get('image_path')
                    })
                elif elem["type"] == "table":
                    caption = f"Table {elem['id']}: {elem['caption']}"
                    visual_references.append({
                        "ref_id": ref_id,
                        "type": "table",
                        "caption": caption,
                        "page": page_num,
                        "data": elem.get('table_data')
                    })
                
                # Track page references
                if page_num != 'N/A':
                    if page_num not in page_references:
                        page_references[page_num] = []
                    page_references[page_num].append(ref_id)

            # Prepare document sections
            document_sections = [
                {
                    "title": "Research Question",
                    "content": question
                },
                {
                    "title": "Analysis",
                    "content": answer
                },
                {
                    "title": "Visual References",
                    "content": "\n".join([ref["caption"] for ref in visual_references])
                }
            ]

            # Generate report prompt
            report_prompt = self._generate_report_prompt(
                question=question,
                answer=answer,
                visual_references=visual_references,
                document_sections=document_sections
            )

            # Generate comprehensive report
            report_content = self.report_model.generate(
                text=report_prompt,
                max_length=self.config.MAX_OUTPUT_LENGTH,
                temperature=self.config.TEMPERATURE,
                top_k=self.config.TOP_K,
                top_p=self.config.TOP_P
            )

            # Format final report
            formatted_report = {
                "title": f"Research Report: {document.title}",
                "document_id": document.id,
                "generated_at": datetime.now().isoformat(),
                "content": report_content,
                "sections": document_sections,
                "visual_references": visual_references,
                "page_references": page_references,
                "metadata": {
                    "source_document": document.title,
                    "generation_params": {
                        "model": "nvidia/nemo-megatron-gpt-1.3B",
                        "temperature": self.config.TEMPERATURE,
                        "max_length": self.config.MAX_OUTPUT_LENGTH
                    },
                    **(metadata if metadata else {})
                }  # Remove extra closing brace and fix indentation
            }
            
            return formatted_report

        except Exception as e:
            raise Exception(f"Error generating research report: {str(e)}")

    def _generate_report_prompt(
        self,
        question: str,
        answer: str,
        visual_references: List[Dict],
        document_sections: List[Dict]
    ) -> str:
        """
        Generate a structured prompt for report generation
        """
        # Create a detailed prompt that instructs the model
        prompt = (
            "Generate a comprehensive research report following this structure:\n\n"
            "1. Research Question:\n"
            f"{question}\n\n"
            "2. Analysis:\n"
            f"{answer}\n\n"
            "3. Visual References:\n"
        )

        # Add visual references
        for ref in visual_references:
            prompt += f"- {ref['caption']} (Page {ref['page']})\n"

        # Add instructions for formatting
        prompt += (
            "\nFormat the report with:\n"
            "- Clear section headings\n"
            "- Proper citations to visual elements\n"
            "- Page references where applicable\n"
            "- Academic tone and structure\n"
            "- Logical flow between sections\n"
        )

        return prompt

    async def save_report(
        self,
        report: Dict,
        save_path: str
    ) -> str:
        """
        Save the generated report to storage
        
        Args:
            report: Generated report dictionary
            save_path: Path to save the report
            
        Returns:
            Path to the saved report
        """
        try:
            # Format report for storage
            storage_format = {
                **report,
                "saved_at": datetime.now().isoformat()
            }

            # Save report (implementation depends on your storage solution)
            # This is a placeholder for the actual storage implementation
            with open(save_path, 'w') as f:
                json.dump(storage_format, f, indent=2)

            return save_path

        except Exception as e:
            raise Exception(f"Error saving research report: {str(e)}")