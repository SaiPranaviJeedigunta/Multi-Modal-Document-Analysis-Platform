from typing import Dict, List, Optional
import torch
from datetime import datetime
from pathlib import Path
import tempfile
from PIL import Image
from pdf2image import convert_from_path
from llama_index import VectorStoreIndex, ServiceContext, Document as LlamaDocument
from llama_index.multi_modal_llms import NvidiaMultiModalLLM
from llama_index.multi_modal_llms.nvidia import NVIDIAMultiModalConfig
from llama_index.schema import ImageNode, TextNode, NodeRelationship
from  app.config.settings import Settings
from ..models.document import Document

class MultiModalRAGService:
    def __init__(self):
        self.settings = Settings()
        self.nvidia_config = NVIDIAMultiModalConfig(
            api_key=self.settings.NVIDIA_API_KEY,
            model_endpoint=self.settings.NVIDIA_MODEL_ENDPOINT
        )
        self.llm = NvidiaMultiModalLLM(config=self.nvidia_config)
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model="local:BAAI/bge-large-en-v1.5"
        )
        
    async def _create_nodes(self, document: Document) -> List[Union[TextNode, ImageNode]]:
        """Create nodes from document content"""
        nodes = []
        
        # Process text content
        if document.summary:
            text_node = TextNode(
                text=document.summary,
                metadata={
                    "document_id": document.id,
                    "type": "summary"
                }
            )
            nodes.append(text_node)
            
        # Process image
        if document.image_link:
            try:
                image = Image.open(document.image_link)
                image_node = ImageNode(
                    image=image,
                    metadata={
                        "document_id": document.id,
                        "type": "cover_image",
                        "page_number": 1
                    }
                )
                nodes.append(image_node)
                
                # Create relationship between text and image
                if nodes:
                    NodeRelationship.from_nodes(
                        parent=text_node,
                        child=image_node,
                        relationship_type="image_context"
                    )
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                
        # Process PDF
        if document.pdf_link:
            try:
                # Convert PDF pages to images
                with tempfile.TemporaryDirectory() as temp_dir:
                    images = convert_from_path(document.pdf_link)
                    for idx, image in enumerate(images, 1):
                        image_node = ImageNode(
                            image=image,
                            metadata={
                                "document_id": document.id,
                                "type": "pdf_page",
                                "page_number": idx
                            }
                        )
                        nodes.append(image_node)
            except Exception as e:
                print(f"Error processing PDF: {str(e)}")
                
        return nodes

    async def process_document(self, document: Document) -> Dict:
        """Process document content with multimodal RAG"""
        try:
            # Create nodes from document content
            nodes = await self._create_nodes(document)
            
            # Create vector store index
            index = VectorStoreIndex(
                nodes,
                service_context=self.service_context
            )
            
            return {
                "document_id": document.id,
                "index": index,
                "processed_at": datetime.now()
            }
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

    async def query_document(
        self,
        document_id: str,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Query document using multimodal RAG"""
        try:
            # Get document index
            index = await self.get_document_index(document_id)
            if not index:
                raise Exception(f"Document index not found for ID: {document_id}")
            
            # Create query engine
            query_engine = index.as_query_engine(
                service_context=self.service_context
            )
            
            # Process query with context if provided
            if context and context.get('image'):
                image_context = ImageNode(
                    image=context['image'],
                    metadata={"type": "query_context"}
                )
                response = query_engine.query(
                    query,
                    image_nodes=[image_context]
                )
            else:
                response = query_engine.query(query)
            
            return {
                "answer": response.response,
                "sources": response.source_nodes,
                "metadata": response.metadata
            }
        except Exception as e:
            raise Exception(f"Error querying document: {str(e)}")

    async def get_document_index(self, document_id: str) -> Optional[VectorStoreIndex]:
        """Retrieve document index from storage"""
        try:
            # Implementation depends on your storage solution
            # This is a placeholder - implement based on your storage
            index_path = Path(self.settings.VECTOR_STORE_PATH) / f"{document_id}.index"
            if index_path.exists():
                return VectorStoreIndex.load_from_disk(
                    str(index_path),
                    service_context=self.service_context
                )
            return None
        except Exception as e:
            raise Exception(f"Error retrieving document index: {str(e)}")

    async def save_document_index(self, document_id: str, index: VectorStoreIndex):
        """Save document index to storage"""
        try:
            # Implementation depends on your storage solution
            index_path = Path(self.settings.VECTOR_STORE_PATH) / f"{document_id}.index"
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index.save_to_disk(str(index_path))
        except Exception as e:
            raise Exception(f"Error saving document index: {str(e)}")