import requests
from typing import Dict, Optional, List
import os
from datetime import datetime
from .config import load_config

class APIClient:
    def __init__(self):
        config = load_config()
        self.base_url = config.get("backend_url", "http://localhost:8000")
        self.session = requests.Session()
        self.token = None

    def _get_headers(self) -> Dict:
        """Get request headers with authentication token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, username: str, password: str) -> dict:
        """Authenticate user and get JWT token"""
        try:
            # Print debug information
            print(f"Attempting to connect to: {self.base_url}/auth/token")
            
            response = requests.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10  # Add timeout
            )
            
            # Print response status and content for debugging
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            return data
            
        except requests.ConnectionError:
            raise Exception("Unable to connect to server. Please ensure the backend server is running at " + self.base_url)
        except requests.Timeout:
            raise Exception("Server connection timed out. Please try again.")
        except requests.RequestException as e:
            raise Exception(f"Login failed: {str(e)}")

    def fetch_documents(self, prompt_count: int = 5) -> Dict:
        """Fetch documents from backend"""
        try:
            response = requests.get(
                f"{self.base_url}/documents",
                params={"prompt_count": prompt_count},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error fetching documents: {str(e)}")

    def get_document_summary(self, document_id: str) -> Dict:
        """Generate or retrieve document summary"""
        try:
            response = requests.get(
                f"{self.base_url}/documents/{document_id}/summary",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error getting document summary: {str(e)}")

    def ask_question(self, document_id: str, question: str) -> Dict:
        """Submit question to Q/A system"""
        try:
            response = requests.post(
                f"{self.base_url}/qa/ask",
                json={"document_id": document_id, "question": question},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error processing question: {str(e)}")

    def search_documents(self, query: str, search_type: str = "all") -> Dict:
        """Search documents and research notes"""
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"query": query, "search_type": search_type},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error searching documents: {str(e)}")

    def generate_report(self, document_id: str, options: Dict) -> Dict:
        """Generate document report"""
        try:
            response = requests.post(
                f"{self.base_url}/documents/{document_id}/report",
                json=options,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error generating report: {str(e)}")