from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.qa import ResearchNote
from ..services.vector_store_service import VectorStoreService
from ..services.nemo_multimodal_service import NeMoMultimodalService
from ..database import get_db
import uuid

class ResearchNotesService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.nemo_service = NeMoMultimodalService()
        self.db = next(get_db())

    async def create_note(
        self,
        document_id: str,
        content: str,
        source_type: str = "manual",
        metadata: Optional[Dict] = None
    ) -> ResearchNote:
        """Create a new research note"""
        try:
            # Generate unique ID for the note
            note_id = str(uuid.uuid4())
            
            # Create research note object
            note = ResearchNote(
                id=note_id,
                document_id=document_id,
                question=metadata.get('question', '') if metadata else '',
                answer=content,
                verified=False,
                created_at=datetime.utcnow()
            )
            
            # Add to database
            self.db.add(note)
            self.db.commit()
            self.db.refresh(note)
            
            # Add to vector store for searching
            await self.vector_store.add_research_note(
                document_id=document_id,
                note=content,
                timestamp=note.created_at
            )
            
            return note
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creating research note: {str(e)}")

    async def get_notes_by_document(
        self,
        document_id: str,
        verified_only: bool = False
    ) -> List[ResearchNote]:
        """Get all research notes for a document"""
        try:
            query = self.db.query(ResearchNote).filter(
                ResearchNote.document_id == document_id
            )
            
            if verified_only:
                query = query.filter(ResearchNote.verified == True)
                
            return query.order_by(ResearchNote.created_at.desc()).all()
            
        except Exception as e:
            raise Exception(f"Error fetching research notes: {str(e)}")

    async def verify_note(
        self,
        note_id: str,
        validator_id: str,
        feedback: Optional[str] = None
    ) -> ResearchNote:
        """Verify a research note"""
        try:
            note = self.db.query(ResearchNote).filter(
                ResearchNote.id == note_id
            ).first()
            
            if not note:
                raise Exception("Research note not found")
                
            note.verified = True
            note.verified_at = datetime.utcnow()
            note.validator_id = validator_id
            if feedback:
                note.feedback = feedback
                
            self.db.commit()
            self.db.refresh(note)
            
            return note
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error verifying research note: {str(e)}")

    async def get_pending_validations(self) -> List[ResearchNote]:
        """Get all research notes pending validation"""
        try:
            return self.db.query(ResearchNote).filter(
                ResearchNote.verified == False
            ).order_by(ResearchNote.created_at.asc()).all()
            
        except Exception as e:
            raise Exception(f"Error fetching pending validations: {str(e)}")

    async def create_qa_derived_note(
        self,
        document_id: str,
        question: str,
        answer: str,
        context: Optional[str] = None
    ) -> ResearchNote:
        """Create a research note from Q&A interaction"""
        try:
            metadata = {
                'question': question,
                'context': context,
                'source_type': 'qa_derived'
            }
            
            return await self.create_note(
                document_id=document_id,
                content=answer,
                source_type='qa_derived',
                metadata=metadata
            )
            
        except Exception as e:
            raise Exception(f"Error creating Q&A derived note: {str(e)}")

    async def create_summary_derived_note(
        self,
        document_id: str,
        summary: str,
        source_content: Optional[str] = None
    ) -> ResearchNote:
        """Create a research note from document summary"""
        try:
            metadata = {
                'source_content': source_content,
                'source_type': 'summary_derived'
            }
            
            return await self.create_note(
                document_id=document_id,
                content=summary,
                source_type='summary_derived',
                metadata=metadata
            )
            
        except Exception as e:
            raise Exception(f"Error creating summary derived note: {str(e)}")

    async def update_note(
        self,
        note_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ResearchNote:
        """Update an existing research note"""
        try:
            note = self.db.query(ResearchNote).filter(
                ResearchNote.id == note_id
            ).first()
            
            if not note:
                raise Exception("Research note not found")
                
            if content:
                note.answer = content
                # Update vector store
                await self.vector_store.update_research_note(
                    document_id=note.document_id,
                    note_id=note_id,
                    new_content=content
                )
                
            if metadata:
                note.metadata = {
                    **(note.metadata or {}),
                    **metadata
                }
                
            self.db.commit()
            self.db.refresh(note)
            
            return note
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error updating research note: {str(e)}")

    async def delete_note(self, note_id: str):
        """Delete a research note"""
        try:
            note = self.db.query(ResearchNote).filter(
                ResearchNote.id == note_id
            ).first()
            
            if not note:
                raise Exception("Research note not found")
                
            # Remove from vector store
            await self.vector_store.remove_research_note(
                document_id=note.document_id,
                note_id=note_id
            )
            
            # Remove from database
            self.db.delete(note)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error deleting research note: {str(e)}")

    async def search_notes(
        self,
        query: str,
        document_id: Optional[str] = None,
        verified_only: bool = False
    ) -> List[Dict]:
        """Search through research notes"""
        try:
            # Search through vector store
            search_results = await self.vector_store.search_document(
                document_id=document_id if document_id else None,
                query=query,
                search_type="notes"
            )
            
            # If verified_only, filter results
            if verified_only:
                note_ids = [result['id'] for result in search_results['results']]
                verified_notes = self.db.query(ResearchNote).filter(
                    ResearchNote.id.in_(note_ids),
                    ResearchNote.verified == True
                ).all()
                verified_ids = {note.id for note in verified_notes}
                search_results['results'] = [
                    result for result in search_results['results']
                    if result['id'] in verified_ids
                ]
                
            return search_results
            
        except Exception as e:
            raise Exception(f"Error searching research notes: {str(e)}")

    async def analyze_notes_trend(
        self,
        document_id: str,
        time_range: Optional[str] = "1w"
    ) -> Dict:
        """Analyze trends in research notes"""
        try:
            # Get notes within time range
            notes = self.db.query(ResearchNote).filter(
                ResearchNote.document_id == document_id
            ).order_by(ResearchNote.created_at.desc()).all()
            
            # Analyze trends using NeMo service
            trend_analysis = await self.nemo_service.analyze_content_trend(
                [note.answer for note in notes]
            )
            
            return {
                'total_notes': len(notes),
                'verified_notes': len([n for n in notes if n.verified]),
                'trend_analysis': trend_analysis
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing research notes trends: {str(e)}")