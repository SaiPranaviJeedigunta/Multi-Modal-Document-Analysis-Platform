import snowflake.connector
import os
import json
from dotenv import load_dotenv
from google.cloud import storage
import re
import requests
import logging
import re
from urllib.parse import unquote
import json
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup as bs
from google.cloud import storage
import urllib.parse
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Also log to a file
file_handler = logging.FileHandler(os.getenv('Error_logs_file', "errors.log"))
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Load environment variables from .env file
load_dotenv()

# Snowflake connection details
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE')
SNOWFLAKE_DATABASE = 'PUBLICATIONS_DB'
SNOWFLAKE_SCHEMA = 'PUBLICATIONS_SCHEMA'
SNOWFLAKE_ROLE = 'ACCOUNTADMIN'
GCS_BUCKET_NAME = os.getenv('BUCKET_NAME')
GCS_JSON_BLOB_NAME = 'cfai_publications/cfa_publications.json'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to clean titles
def clean_title(title):
    return title.replace('\n', ' ').strip()

# Extract PDF link from detail page
def extract_detail_data(driver):
    logger.info("Extracting PDF link from detail page...")
    detail_soup = bs(driver.page_source, 'html.parser')
    pdf_section = detail_soup.find('a', class_='content-asset content-asset--primary')
    pdf_link = pdf_section['href'] if pdf_section else 'N/A'
    if pdf_link and not pdf_link.startswith('http'):
        pdf_link = 'https://rpc.cfainstitute.org' + pdf_link
    return pdf_link

def download_file(url, download_folder, filename):
    if url and url != 'N/A':
        try:
            logger.info(f"Downloading: {url}")
            response = requests.get(url)
            response.raise_for_status()
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)
            safe_filename = filename.replace('/', '-')
            file_path = os.path.join(download_folder, safe_filename)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            logger.info(f"Downloaded: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
    return None

def clean_filename(filename):
    return re.sub(r'\?.*$', '', filename)

def generate_authenticated_url(bucket_name, destination_blob_name):
    """Generate an authenticated URL for GCS."""
    return f"https://storage.googleapis.com/{bucket_name}/{urllib.parse.quote(destination_blob_name)}"

def upload_to_gcs(bucket_name, source_folder, destination_blob_name):
    """Uploads specific folders to a GCS bucket and returns URLs for the uploaded files."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Define folders to exclude (e.g., venv)
    exclude_dirs = {'venv', '__pycache__', '.git','dags', 'logs'}
    publication_links = {}

    # Upload each publication folder, excluding any irrelevant folders
    for publication_folder in os.listdir(source_folder):
        folder_path = os.path.join(source_folder, publication_folder)

        if os.path.isdir(folder_path) and publication_folder not in exclude_dirs:
            pdf_gcs_link = None
            image_gcs_link = None

            # Upload files and capture GCS links
            for dirpath, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    # File paths and cleaned name
                    local_file_path = os.path.join(dirpath, filename)
                    clean_name = clean_filename(filename)
                    relative_path = os.path.relpath(os.path.join(dirpath, clean_name), source_folder)
                    blob = bucket.blob(os.path.join(destination_blob_name, relative_path))

                    # Upload file
                    blob.upload_from_filename(local_file_path)
                    gcs_link = generate_authenticated_url(bucket_name, os.path.join(destination_blob_name, relative_path))

                    # Store GCS link based on file type
                    if clean_name.endswith('.pdf'):
                        pdf_gcs_link = gcs_link
                    elif clean_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_gcs_link = gcs_link

            # Add GCS links to the publication dictionary
            publication_links[publication_folder] = {
                "pdf_gcs_link": pdf_gcs_link,
                "image_gcs_link": image_gcs_link
            }

    return publication_links

def upload_json_to_gcs(bucket_name, json_file_name, destination_blob_name):
    """Uploads the JSON file to GCS."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(json_file_name)
    logger.info(f"Uploaded JSON file to GCS: gs://{bucket_name}/{destination_blob_name}")

def scrape_publications():
    logger.info("Starting data extraction...")
    gcs_bucket_name = os.getenv('BUCKET_NAME')
    json_file_name = os.getenv('JSON_FILE_NAME', 'cfa_publications.json')
    gcs_path = os.getenv('GCS_PATH', 'cfai_publications')
    service = Service('/usr/local/bin/geckodriver')  # You may need to specify the path to your geckodriver
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    all_data = []
    seen_titles = set()
    publication_index = 1

    try:
        driver.get("https://rpc.cfainstitute.org/en/research-foundation/publications#sort=%40officialz32xdate%20descending&f:SeriesContent=[Research%20Foundation]")
        while True:
            logger.info("Waiting for publication items to load...")
            WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "RPCAllsiteSearchResultList")))
            soup = bs(driver.page_source, 'html.parser')
            publications = soup.find_all('div', class_='coveo-result-frame')
            if not publications:
                logger.warning("No publications found on the page.")
                break
            for publication in publications:
                title_element = publication.find('h4', class_='coveo-title')
                title = title_element.get_text(strip=True) if title_element else 'N/A'
                title = clean_title(title)
                if title in seen_titles:
                    logger.warning(f"Duplicate publication found: {title}. Skipping...")
                    continue
                seen_titles.add(title)
                detail_link = title_element.find('a')['href'] if title_element and title_element.find('a') else None
                if detail_link and not detail_link.startswith('http'):
                    detail_link = 'https://rpc.cfainstitute.org' + detail_link
                date_element = publication.find('span', class_='date')
                publication_date = date_element.get_text(strip=True) if date_element else 'N/A'
                image_element = publication.find('img', class_='coveo-result-image')
                image_src = image_element['src'] if image_element else 'N/A'
                if image_src != 'N/A' and not image_src.startswith('http'):
                    image_src = 'https://rpc.cfainstitute.org' + image_src
                summary_element = publication.find('div', class_='result-body')
                summary = summary_element.get_text(strip=True) if summary_element else 'N/A'
                pdf_link = 'N/A'
                if detail_link:
                    logger.info(f"Loading detail page for: {title}...")
                    driver.get(detail_link)
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "grid__item--article-element")))
                    pdf_link = extract_detail_data(driver)
                    publication_folder = clean_title(title)
                    if not os.path.exists(publication_folder):
                        os.makedirs(publication_folder)
                    download_file(pdf_link, publication_folder, f"{title}.pdf")
                    if image_src != 'N/A':
                        file_extension = image_src.split('.')[-1]
                        download_file(image_src, publication_folder, f"{title}.{file_extension}")
                    driver.back()
                    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "RPCAllsiteSearchResultList")))
                
                # Add GCS links to all_data
                all_data.append({
                    'Index': publication_index,
                    'Title': title,
                    'Date': publication_date,
                    'Summary': summary,
                    'PDF Link': pdf_link,  # Keep the local PDF link for downloading
                    'Image Link': image_src  # Local image link for downloading
                })
                publication_index += 1
            
            try:
                next_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "coveo-pager-next")))
                if 'disabled' in next_button.get_attribute('class'):
                    logger.info("No more pages to scrape.")
                    break
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                next_button.click()
                WebDriverWait(driver, 10).until(EC.staleness_of(next_button))
            except Exception as e:
                logger.error(f"Error navigating to the next page: {e}")
                break

        # Upload files to GCS and get their links
        publication_links = upload_to_gcs(gcs_bucket_name, '.', gcs_path)

        # Append GCS links to JSON data
        for item in all_data:
            title_key = clean_title(item['Title'])
            if title_key in publication_links:
                item['pdf_gcs_link'] = publication_links[title_key].get('pdf_gcs_link')
                item['image_gcs_link'] = publication_links[title_key].get('image_gcs_link')
            else:
                item['pdf_gcs_link'] = None
                item['image_gcs_link'] = None

        # Save JSON to file
        with open(json_file_name, 'w', encoding='utf-8') as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to {json_file_name}")

        # Upload JSON to GCS
        upload_json_to_gcs(gcs_bucket_name, json_file_name, gcs_path + '/' + json_file_name)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        driver.quit()

def create_or_replace_snowflake_resources():
    """Create or replace Snowflake resources including storage integration, database, schema, and stage."""
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            role=SNOWFLAKE_ROLE
        )

        cursor = conn.cursor()

        # Execute SQL statements
        sql_statements = [
            # Drop storage integration if it exists
            "DROP STORAGE INTEGRATION IF EXISTS gcs_int;",
            # Create storage integration
            """
            CREATE OR REPLACE STORAGE INTEGRATION gcs_int
            TYPE = EXTERNAL_STAGE
            STORAGE_PROVIDER = 'GCS'
            ENABLED = TRUE
            STORAGE_ALLOWED_LOCATIONS = ('gcs://cfa_scraped_data/');
            """,
            # Describe storage integration
            "DESC STORAGE INTEGRATION gcs_int;",
            # Create or replace database
            "CREATE DATABASE IF NOT EXISTS publications_db;",
            # Create or replace schema
            "CREATE SCHEMA IF NOT EXISTS publications_db.publications_schema;",
            # Create or replace role
            "CREATE ROLE IF NOT EXISTS DATA_INGEST_ROLE;",
            # Grant usage on database
            "GRANT USAGE ON DATABASE publications_db TO ROLE DATA_INGEST_ROLE;",
            # Grant usage on schema
            "GRANT USAGE ON SCHEMA publications_db.publications_schema TO ROLE DATA_INGEST_ROLE;",
            # Grant create stage on schema
            "GRANT CREATE STAGE ON SCHEMA publications_db.publications_schema TO ROLE DATA_INGEST_ROLE;",
            # Grant usage on integration
            "GRANT USAGE ON INTEGRATION gcs_int TO ROLE DATA_INGEST_ROLE;",
            # Use the specific schema
            "USE SCHEMA publications_db.publications_schema;",
            # Create or replace file format
            """
            CREATE OR REPLACE FILE FORMAT my_json_format
            TYPE = 'JSON';
            """,
            # Drop stage if it exists
            "DROP STAGE IF EXISTS my_gcs_stage;",
            # Create stage
            """
            CREATE STAGE my_gcs_stage
            URL = 'gcs://cfa_scraped_data/'
            STORAGE_INTEGRATION = gcs_int
            FILE_FORMAT = my_json_format;
            """
        ]

        for statement in sql_statements:
            cursor.execute(statement)
            print(f"Executed: {statement.strip()}")

        print("Snowflake resources have been successfully created or replaced.")

    except snowflake.connector.errors.DatabaseError as e:
        print(f"An error occurred: {e}")

    finally:
        cursor.close()
        conn.close()

def load_json_from_gcs(bucket_name, json_blob_name):
    """Load JSON data from a GCS bucket."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(json_blob_name)
    json_data = blob.download_as_text()
    return json.loads(json_data)

def list_gcs_files(bucket_name):
    """List all files in a GCS bucket with their GCS links."""
    client = storage.Client()
    blobs = client.list_blobs(bucket_name)
    files = {blob.name: f"gs://{bucket_name}/{blob.name}" for blob in blobs}
    return files

def normalize_title(title):
    """Normalize title by removing special characters for matching."""
    if not title:
        return ""
    # Decode any URL-encoded characters
    decoded_title = unquote(title)
    # Remove special characters and normalize spacing
    normalized = re.sub(r'[^\w\s]', '', decoded_title).replace(' ', '').lower()
    return normalized

def create_table_and_load_data(publications):
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        role=SNOWFLAKE_ROLE
    )

    try:
        cursor = conn.cursor()

        # Create the publications_data table
        create_table_query = """
        CREATE OR REPLACE TABLE publications_data (
            title STRING,
            summary STRING,
            image_link STRING,
            pdf_link STRING
        );
        """
        cursor.execute(create_table_query)
        print("Table 'publications_data' created successfully.")

        # List all files in the GCS bucket
        gcs_files = list_gcs_files(GCS_BUCKET_NAME)

        # Load data into the publications_data table
        for pub in publications:
            title = pub.get("Title")
            summary = pub.get("Summary")

            # Normalize title for matching
            norm_title = normalize_title(title)
            
            # Enhanced logic to identify PDF links, ignoring image files
            pdf_link = next((link for file_name, link in gcs_files.items()
                             if norm_title in normalize_title(file_name) and 
                             (file_name.endswith(".pdf") or
                              ("publications" in file_name.lower() and not file_name.endswith((".jpg", ".png"))))),
                             None)
            
            # Check for PNG files if available, otherwise fall back to .jpg
            image_link = next((link for file_name, link in gcs_files.items()
                               if norm_title in normalize_title(file_name) and file_name.endswith(".png")), None)

            # If no PNG is found, check for a .jpg image
            if not image_link:
                image_link = next((link for file_name, link in gcs_files.items()
                                   if norm_title in normalize_title(file_name) and file_name.endswith(".jpg")), None)

            # Log details for verification
            print(f"PDF link for '{title}': {pdf_link if pdf_link else 'Not Found'}")
            print(f"Image link for '{title}': {image_link if image_link else 'Not Found'}")

            # Insert data into the table
            insert_query = """
            INSERT INTO publications_data (title, summary, image_link, pdf_link)
            VALUES (%s, %s, %s, %s);
            """
            cursor.execute(insert_query, (title, summary, image_link, pdf_link))

        print("Data loaded into 'publications_data' successfully.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()

def loadtosnowflake():
    """Main function to load JSON data and populate the Snowflake table."""
    # Load publications from GCS
    publications = load_json_from_gcs(GCS_BUCKET_NAME, GCS_JSON_BLOB_NAME)
    
    # Create table and load data into Snowflake
    create_table_and_load_data(publications)

# Define the DAG
with DAG(
    dag_id='cfai_publications_dag',
    schedule_interval='@daily',  # Set the desired schedule interval
    start_date=datetime(2024, 10, 26),  # Change to your desired start date
    catchup=False,
    tags=['cfai', 'publications']
) as dag:

    scrape_publications_op = PythonOperator(
        task_id='scrape_publications',
        python_callable=scrape_publications
    )

    load_to_snowflake_op = PythonOperator(
        task_id='load_to_snowflake',
        python_callable=loadtosnowflake
    )

    # Set task dependencies
    scrape_publications_op >> load_to_snowflake_op