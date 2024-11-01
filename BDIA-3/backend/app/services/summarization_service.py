from typing import Optional, Dict, List
from datetime import datetime
from app.config.settings import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import ChatNVIDIA

class SummarizationService:
    def __init__(self):
        self.settings = Settings()
        # Initialize the NVIDIA AI model
        self.model = ChatNVIDIA(
            api_key=self.settings.NVIDIA_API_KEY,
        )
        
        # Initialize text splitter for long documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def generate_document_summary(self, document_content: str, pdf_path: Optional[str] = None) -> Dict:
        """Generate a comprehensive document summary"""
        try:
            # Split text into chunks if it's too long
            chunks = self.text_splitter.split_text(document_content)
            
            # Generate summary prompt
            summary_prompt = (
                "Generate a comprehensive summary of this document, "
                "including key findings, methodology, and conclusions. "
                "Format the response with clear sections."
            )
            
            # Generate summary using the NVIDIA model
            summary = await self.model.agenerate(
                [summary_prompt + "\n\nDocument: " + chunk for chunk in chunks]
            )

            return {
                "summary": summary.generations[0][0].text,
                "metadata": {
                    "chunks_processed": len(chunks),
                    "text_processed": True,
                    "generated_at": str(datetime.now())
                }
            }

        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

    async def generate_research_note_summary(self, qa_interactions: List[Dict]) -> str:
        """Generate a summary from Q&A interactions"""
        try:
            # Prepare context from Q&A interactions
            qa_context = "\n\n".join([
                f"Q: {qa['question']}\nA: {qa['answer']}"
                for qa in qa_interactions
            ])

            research_note_prompt = (
                "Based on the following Q&A interactions, provide a coherent "
                "research note that synthesizes the key insights and findings. "
                "Include relevant cross-references and maintain academic tone.\n\n"
                f"Q&A Context:\n{qa_context}"
            )
            
            response = await self.model.agenerate([research_note_prompt])
            return response.generations[0][0].text

        except Exception as e:
            raise Exception(f"Error generating research note summary: {str(e)}")

    async def analyze_content_trend(self, contents: List[str]) -> Dict:
        """Analyze trends in content"""
        try:
            combined_content = "\n---\n".join(contents)
            trend_prompt = (
                "Analyze the following content for trends and patterns. "
                "Provide a summary of key trends, changes, and confidence level.\n\n"
                f"Content:\n{combined_content}"
            )
            
            response = await self.model.agenerate([trend_prompt])
            analysis = response.generations[0][0].text
            
            return {
                "trend_summary": analysis,
                "key_changes": [],  # You can implement more detailed analysis if needed
                "confidence": "medium"  # You can implement confidence scoring if needed
            }

        except Exception as e:
            raise Exception(f"Error analyzing content trend: {str(e)}")