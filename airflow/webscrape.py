import os
import requests
import logging
import re
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from google.cloud import storage
import urllib.parse

# Load environment variables from .env file
load_dotenv()

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
    service = Service()  # You may need to specify the path to your geckodriver
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

if __name__ == "__main__":
    scrape_publications()
