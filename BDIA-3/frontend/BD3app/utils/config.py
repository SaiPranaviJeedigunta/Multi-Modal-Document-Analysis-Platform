import os
from typing import Dict

def load_config() -> Dict:
    """Load configuration settings"""
    return {
        "backend_url": os.getenv("BACKEND_URL", "http://localhost:8000"),
        "api_version": os.getenv("API_VERSION", "v1")
    }