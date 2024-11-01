import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from snowflake.connector import connect
from google.cloud import storage
from dotenv import load_dotenv
import fitz  # PyMuPDF
import os
from openai import OpenAI

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI()

# Snowflake connection configurations
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

# NVIDIA API configurations
API_KEY = os.getenv("NVIDIA_API_KEY")
TRITON_SERVER_URL = "https://integrate.api.nvidia.com/v1"

# GCP configurations
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")

if not API_KEY or not TRITON_SERVER_URL:
    logger.error("NVIDIA API_KEY or TRITON_SERVER_URL not found in environment variables")
    raise EnvironmentError("NVIDIA API_KEY or TRITON_SERVER_URL not found in environment variables")

# Establish connection to Snowflake
def get_snowflake_connection():
    try:
        logger.info("Connecting to Snowflake...")
        conn = connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
        logger.info("Successfully connected to Snowflake")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Snowflake: {str(e)}")

# Fetch PDF URLs from Snowflake
def fetch_pdf_urls_from_snowflake(conn):
    """Fetch PDF URLs from Snowflake."""
    try:
        logger.info("Fetching PDF URLs from Snowflake...")
        cursor = conn.cursor()
        cursor.execute("SELECT PDF_LINK FROM PUBLICATIONS_DATA")
        pdf_urls = [row[0] for row in cursor.fetchall()]
        logger.info(f"Fetched {len(pdf_urls)} PDF URLs from Snowflake")
        return pdf_urls
    except Exception as e:
        logger.error(f"Error fetching PDF URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching PDF URLs: {str(e)}")

# Download a PDF from GCS
def download_pdf_from_gcs(pdf_url, local_path):
    """Download a PDF from GCS."""
    try:
        logger.info(f"Downloading PDF from GCS: {pdf_url}")
        if pdf_url.startswith("gs://"):
            pdf_url = pdf_url.replace("gs://", "", 1)

        bucket_name, object_key = pdf_url.split('/', 1)
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_key)
        blob.download_to_filename(local_path)
        logger.info(f"Downloaded PDF to {local_path}")
    except Exception as e:
        logger.error(f"Error downloading PDF from GCS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF from GCS: {str(e)}")

# Extract text from a PDF using PyMuPDF
def extract_text_from_pdf(pdf_path):
    try:
        logger.info(f"Extracting text from PDF: {pdf_path}")
        with fitz.open(pdf_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text")
        logger.info("Successfully extracted text from PDF")
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

def generate_summary_from_text(extracted_text):
    """Generate a summary using the NVIDIA model."""
    try:
        # Log the start of summary generation
        logger.info("Generating summary using NVIDIA API...")
        
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
            stream=False
        )

        # Log the full API response for debugging
        logger.info(f"Full API Response: {completion_response}")

        # Ensure the response contains 'choices' with a 'message'
        if not hasattr(completion_response, 'choices') or not hasattr(completion_response.choices[0], 'message'):
            raise ValueError("Invalid response format from NVIDIA API")

        # Collect the generated summary from 'message.content'
        summary_text = completion_response.choices[0].message.content

        logger.info("Successfully generated summary")
        return summary_text
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/process-pdfs")
def process_pdfs():
    try:
        logger.info("Starting PDF processing...")

        # Connect to Snowflake
        conn = get_snowflake_connection()
        
        # Fetch PDF URLs
        pdf_urls = fetch_pdf_urls_from_snowflake(conn)
        
        # Process each PDF URL
        summaries = []
        for pdf_url in pdf_urls:
            local_path = f"/tmp/{os.path.basename(pdf_url)}"
            
            # Download the PDF from GCS
            download_pdf_from_gcs(pdf_url, local_path)
            
            # Extract text from the PDF
            extracted_text = extract_text_from_pdf(local_path)
            if not extracted_text:
                logger.warning(f"No text found in PDF: {pdf_url}")
                continue
            
            # Generate summary from extracted text
            summary = generate_summary_from_text(extracted_text)
            summaries.append({"pdf_url": pdf_url, "summary": summary})
            
            # Clean up temporary file
            os.remove(local_path)
            logger.info(f"Processed and removed temporary file: {local_path}")
        
        logger.info("Successfully processed all PDFs")
        return JSONResponse(content={"summaries": summaries})
    
    except Exception as e:
        logger.error(f"Error processing PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")
