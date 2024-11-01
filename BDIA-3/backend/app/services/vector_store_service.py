from llama_index import (
    VectorStoreIndex,
    Document as LlamaDocument,
    StorageContext,
    ServiceContext,
    Node
)
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
import pickle

class VectorStoreService:
    def __init__(self):
        self.storage_context = StorageContext.from_defaults()
        self.service_context = ServiceContext.from_defaults()
        self.document_indices = {}
        self.research_notes_indices = {}
        self.document_chunks = {}
        self.chunk_size = 500  # Default chunk size

    async def add_document(self, document_id: str, content: str, metadata: Optional[Dict] = None):
        """Add document to vector store"""
        try:
            # Create document nodes
            nodes = [
                Node(
                    text=content,
                    metadata={
                        "document_id": document_id,
                        **(metadata or {})
                    }
                )
            ]
            
            # Create or update index for this document
            self.document_indices[document_id] = VectorStoreIndex(
                nodes,
                storage_context=self.storage_context,
                service_context=self.service_context
            )
            
        except Exception as e:
            raise Exception(f"Error adding document to vector store: {str(e)}")

    async def search_document(
        self,
        query: str,
        document_id: Optional[str] = None,
        search_type: str = "all",
        top_k: int = 5
    ) -> Dict:
        """Search through documents"""
        try:
            if document_id and document_id in self.document_indices:
                # Search specific document
                index = self.document_indices[document_id]
                retriever = index.as_retriever(similarity_top_k=top_k)
                nodes = retriever.retrieve(query)
            else:
                # Search all documents
                all_nodes = []
                for doc_index in self.document_indices.values():
                    retriever = doc_index.as_retriever(similarity_top_k=top_k)
                    nodes = retriever.retrieve(query)
                    all_nodes.extend(nodes)
                nodes = sorted(all_nodes, key=lambda x: x.score, reverse=True)[:top_k]
            
            return {
                "results": [
                    {
                        "id": node.metadata.get("document_id"),
                        "content": node.text,
                        "score": node.score,
                        "metadata": node.metadata
                    }
                    for node in nodes
                ]
            }
            
        except Exception as e:
            raise Exception(f"Error searching documents: {str(e)}")

    async def search_research_notes(self, document_id: str, query: str, top_k: int = 5):
        """Search through research notes"""
        if document_id not in self.research_notes_indices:
            return []
        
        query_engine = self.research_notes_indices[document_id].as_query_engine()
        response = query_engine.query(query)
        return response.source_nodes[:top_k]

    async def add_research_note(
        self,
        document_id: str,
        note: str,
        timestamp: datetime,
        metadata: Optional[Dict] = None
    ):
        """Add research note to vector store"""
        try:
            node = Node(
                text=note,
                metadata={
                    "document_id": document_id,
                    "timestamp": timestamp.isoformat(),
                    "type": "research_note",
                    **(metadata or {})
                }
            )
            
            if document_id not in self.document_indices:
                self.document_indices[document_id] = VectorStoreIndex(
                    [node],
                    storage_context=self.storage_context,
                    service_context=self.service_context
                )
            else:
                self.document_indices[document_id].insert_nodes([node])
                
        except Exception as e:
            raise Exception(f"Error adding research note: {str(e)}")

    async def update_research_note(
        self,
        document_id: str,
        note_id: str,
        new_content: str
    ):
        """Update existing research note"""
        try:
            if document_id not in self.document_indices:
                raise Exception("Document not found in vector store")
                
            # Remove old note and add updated one
            await self.remove_research_note(document_id, note_id)
            await self.add_research_note(
                document_id=document_id,
                note=new_content,
                timestamp=datetime.utcnow(),
                metadata={"note_id": note_id}
            )
            
        except Exception as e:
            raise Exception(f"Error updating research note: {str(e)}")

    async def remove_research_note(self, document_id: str, note_id: str):
        """Remove research note from vector store"""
        try:
            if document_id not in self.document_indices:
                return
                
            index = self.document_indices[document_id]
            # Filter out the note to be removed
            nodes = [
                node for node in index.docstore.docs.values()
                if node.metadata.get("note_id") != note_id
            ]
            
            # Recreate index without the removed note
            self.document_indices[document_id] = VectorStoreIndex(
                nodes,
                storage_context=self.storage_context,
                service_context=self.service_context
            )
            
        except Exception as e:
            raise Exception(f"Error removing research note: {str(e)}")

    def save_indices(self, path: str):
        """Save indices to disk"""
        with open(path, 'wb') as f:
            pickle.dump({
                'documents': self.document_indices,
                'notes': self.research_notes_indices
            }, f)

    def load_indices(self, path: str):
        """Load indices from disk"""
        with open(path, 'rb') as f:
            indices = pickle.load(f)
            self.document_indices = indices['documents']
            self.research_notes_indices = indices['notes']

    async def chunk_document(self, content: str) -> List[Dict]:
        """Chunk document for efficient processing"""
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for line in content.split('\n'):
            line_size = len(line.split())
            if current_size + line_size > self.chunk_size:
                chunks.append({
                    "content": current_chunk,
                    "size": current_size
                })
                current_chunk = line
                current_size = line_size
            else:
                current_chunk += f"\n{line}"
                current_size += line_size
            
        if current_chunk:
            chunks.append({
                "content": current_chunk,
                "size": current_size
            })
        
        return chunks

    async def update_document_chunks(self, document_id: str, chunks: List[Dict]):
        """Update document chunks in cache"""
        self.document_chunks[document_id] = chunks
        await self.create_document_index(document_id, chunks)

    async def create_document_index(self, document_id: str, content: str):
        """Create or update document index"""
        documents = [LlamaDocument(text=content)]
        self.document_indices[document_id] = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            service_context=self.service_context
        )

    async def create_research_notes_index(self, document_id: str, notes: List[str]):
        """Create or update research notes index"""
        documents = [LlamaDocument(text=note) for note in notes]
        self.research_notes_indices[document_id] = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            service_context=self.service_context
        )