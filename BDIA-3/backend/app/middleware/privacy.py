from fastapi import Request, HTTPException
from typing import List, Dict, Any
import hashlib
import re
from datetime import datetime

class PrivacyMiddleware:
    def __init__(self):
        # Define sensitive fields and their patterns
        self.sensitive_patterns = {
            "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "password": r"(?i)(password|pwd)[\s:=]+\S+",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        }
        
        # Fields that should be anonymized rather than blocked
        self.anonymize_fields = ["email", "phone"]
        
        # Salt for hashing
        self.salt = datetime.now().strftime("%Y%m%d")
        
    async def process_request(self, request: Request):
        """Process request to ensure data privacy"""
        try:
            # Get request body
            body = await request.json()
            
            # Check for blocked sensitive data
            self._check_sensitive_data(body)
            
            # Anonymize allowed sensitive data
            anonymized_body = self._anonymize_data(body)
            
            # Store processed body in request state
            request.state.processed_body = anonymized_body
            
        except ValueError:
            # If request has no JSON body, skip processing
            pass
        
    def _check_sensitive_data(self, data: Dict[str, Any]):
        """Check for sensitive data patterns that should be blocked"""
        data_str = str(data).lower()
        
        for field, pattern in self.sensitive_patterns.items():
            # Skip fields that should be anonymized
            if field in self.anonymize_fields:
                continue
                
            # Check for sensitive patterns
            if re.search(pattern, data_str):
                raise HTTPException(
                    status_code=400,
                    detail=f"Request contains sensitive data: {field}. Please remove before submitting."
                )
    
    def _anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data that's allowed but should be masked"""
        if isinstance(data, dict):
            return {k: self._anonymize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._anonymize_data(item) for item in data]
        elif isinstance(data, str):
            return self._anonymize_string(data)
        else:
            return data
            
    def _anonymize_string(self, text: str) -> str:
        """Anonymize sensitive patterns in a string"""
        for field, pattern in self.sensitive_patterns.items():
            # Only anonymize fields in anonymize_fields
            if field not in self.anonymize_fields:
                continue
                
            # Find all matches
            matches = re.finditer(pattern, text)
            
            # Replace each match with a hashed version
            for match in matches:
                sensitive_data = match.group(0)
                hashed_data = self._hash_sensitive_data(sensitive_data)
                text = text.replace(sensitive_data, f"[REDACTED:{hashed_data[:8]}]")
                
        return text
    
    def _hash_sensitive_data(self, data: str) -> str:
        """Create a salted hash of sensitive data"""
        salted_data = f"{data}{self.salt}"
        return hashlib.sha256(salted_data.encode()).hexdigest()
    
    def _is_json_serializable(self, value: Any) -> bool:
        """Check if a value can be JSON serialized"""
        try:
            import json
            json.dumps(value)
            return True
        except (TypeError, OverflowError):
            return False