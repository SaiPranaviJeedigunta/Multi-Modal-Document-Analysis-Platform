from typing import Dict, List, Optional
from datetime import datetime
from ..models.qa import ResearchNote

class ValidationService:
    def __init__(self):
        self.pending_validations: Dict[str, List[ResearchNote]] = {}
        self.validated_notes: Dict[str, List[ResearchNote]] = {}

    async def submit_for_validation(self, note: ResearchNote) -> str:
        """Submit a research note for validation"""
        if note.document_id not in self.pending_validations:
            self.pending_validations[note.document_id] = []
        
        self.pending_validations[note.document_id].append(note)
        return note.id

    async def validate_note(
        self,
        note_id: str,
        validator: str,
        is_valid: bool,
        feedback: Optional[str] = None
    ) -> ResearchNote:
        """Validate a research note"""
        # Find note in pending validations
        for doc_id, notes in self.pending_validations.items():
            for note in notes:
                if note.id == note_id:
                    note.verified = is_valid
                    note.verified_at = datetime.now()
                    note.validator = validator
                    note.feedback = feedback
                    
                    # Move to validated notes
                    if doc_id not in self.validated_notes:
                        self.validated_notes[doc_id] = []
                    self.validated_notes[doc_id].append(note)
                    
                    # Remove from pending
                    self.pending_validations[doc_id].remove(note)
                    return note
        
        raise Exception("Note not found in pending validations")

    async def get_pending_validations(self, document_id: Optional[str] = None) -> List[ResearchNote]:
        """Get pending validations, optionally filtered by document"""
        if document_id:
            return self.pending_validations.get(document_id, [])
        return [
            note
            for notes in self.pending_validations.values()
            for note in notes
        ]

    async def get_validated_notes(self, document_id: Optional[str] = None) -> List[ResearchNote]:
        """Get validated notes, optionally filtered by document"""
        if document_id:
            return self.validated_notes.get(document_id, [])
        return [
            note
            for notes in self.validated_notes.values()
            for note in notes
        ]