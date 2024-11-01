import snowflake.connector
import os
import json
from dotenv import load_dotenv
from google.cloud import storage
import re

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
    normalized = re.sub(r'[^\w\s]', '', title).replace(' ', '').lower()
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
            pdf_link = next((link for file_name, link in gcs_files.items()
                             if norm_title in normalize_title(file_name) and file_name.endswith(".pdf")), None)
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

def main():
    """Main function to orchestrate Snowflake resource creation and data loading."""
    # Step 1: Create or replace Snowflake resources
    create_or_replace_snowflake_resources()

    # Step 2: Load publications from GCS
    publications = load_json_from_gcs(GCS_BUCKET_NAME, GCS_JSON_BLOB_NAME)

    # Step 3: Create table and load data into Snowflake
    create_table_and_load_data(publications)

if __name__ == "__main__":
    main()
