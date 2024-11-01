import fitz  # PyMuPDF
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# NVIDIA API configurations
API_KEY = os.getenv("NVIDIA_API_KEY")
TRITON_SERVER_URL = "https://integrate.api.nvidia.com/v1"

if not API_KEY or not TRITON_SERVER_URL:
    raise EnvironmentError("NVIDIA API_KEY or TRITON_SERVER_URL not found in environment variables")

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyMuPDF."""
    try:
        with fitz.open(pdf_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text")
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return None

def generate_summary_from_text(extracted_text):
    """Generate a summary using the NVIDIA model."""
    try:
        # Create OpenAI client
        openai_client = OpenAI(
            base_url=TRITON_SERVER_URL,
            api_key=API_KEY
        )

        # Prepare prompt message
        prompt_message = [{
            'role': 'user',
            'content': f"Summarize the following text in a concise way: \n{extracted_text}"
        }]

        # Make completion request
        completion_response = openai_client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=prompt_message,
            temperature=0.2,
            top_p=0.7,
            max_tokens=150,
            stream=True
        )

        # Collect the generated summary
        summary_text = ""
        for chunk in completion_response:
            if chunk.choices[0].delta.content is not None:
                summary_text += chunk.choices[0].delta.content

        return summary_text
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

def summarize_pdf_document(pdf_file_path):
    """Extract text from a PDF and generate a summary."""
    print(f"Processing PDF file at: {pdf_file_path}")

    # Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_file_path)
    if not extracted_text:
        print("No text extracted from PDF")
        return

    print("Extracted Text:", extracted_text[:500])  # Print the first 500 characters of extracted text for validation

    # Generate summary
    summary = generate_summary_from_text(extracted_text)
    if summary:
        print("Generated Summary:", summary)
    else:
        print("Failed to generate summary")

if __name__ == "__main__":
    # Define path to your PDF file
    pdf_path = "samplepdf.pdf"  # Replace with the actual path to your test PDF

    # Check if the PDF file exists
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
    else:
        summarize_pdf_document(pdf_path)





from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# FastAPI app initialization
app = FastAPI()

# Allow CORS for all origins (only for development/testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows all origins; for production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NVIDIA API configurations
API_KEY = os.getenv("NVIDIA_API_KEY")
TRITON_SERVER_URL = "https://integrate.api.nvidia.com/v1"

if not API_KEY or not TRITON_SERVER_URL:
    raise EnvironmentError("NVIDIA API_KEY or TRITON_SERVER_URL not found in environment variables")

class SummarizeResponse(BaseModel):
    summary: str

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyMuPDF."""
    try:
        with fitz.open(pdf_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text")
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

def generate_summary_from_text(extracted_text):
    """Generate a summary using the NVIDIA model."""
    try:
        # Create OpenAI client
        openai_client = OpenAI(
            base_url=TRITON_SERVER_URL,
            api_key=API_KEY
        )

        # Prepare prompt message
        prompt_message = [{
            'role': 'user',
            'content': f"Summarize the following text in a concise way: \n{extracted_text}"
        }]

        # Make completion request
        completion_response = openai_client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=prompt_message,
            temperature=0.2,
            top_p=0.7,
            max_tokens=150,
            stream=True
        )

        # Collect the generated summary
        summary_text = ""
        for chunk in completion_response:
            if chunk.choices[0].delta.content is not None:
                summary_text += chunk.choices[0].delta.content

        return summary_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

# Endpoint to summarize the PDF content
@app.post("/summarize/", response_model=SummarizeResponse)
async def summarize_pdf(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file received")

    # Save the uploaded PDF to a temporary location
    pdf_path = f"/tmp/{file.filename}"
    try:
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(await file.read())

        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(pdf_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No text found in PDF")

        # Generate summary from extracted text
        summary = generate_summary_from_text(extracted_text)
        if summary:
            return JSONResponse(content={"summary": summary})
        else:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

# Root route for basic check
@app.get("/")
def read_root():
    return {"message": "Welcome to the PDF Summary API!"}
