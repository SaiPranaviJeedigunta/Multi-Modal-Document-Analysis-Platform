import requests
import os

# Load the FastAPI backend URL from .env or set a default
backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def fetch_documents(prompt_count=5):
    """
    Fetches documents from the FastAPI /explore_documents endpoint.

    Args:
        prompt_count (int): Number of documents to fetch. Defaults to 5.

    Returns:
        dict: JSON response containing document data or an error message.
    """
    try:
        # Make a GET request to the /explore_documents endpoint with prompt_count as a query parameter
        response = requests.get(f"{backend_url}/explore_documents", params={"prompt_count": prompt_count})
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        
        # Parse the JSON response and return it
        return response.json()
    
    except requests.RequestException as e:
        print(f"Error fetching documents from {backend_url}/explore_documents: {e}")
        # Return an empty dictionary or error information to handle in the Streamlit frontend
        return {"documents": [], "count": 0}
