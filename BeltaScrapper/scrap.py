import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import re
import time
from markdownify import markdownify as md
import os
import requests
from urllib.parse import urlencode, urljoin, urlparse
from bs4 import BeautifulSoup
import uuid
from datetime import datetime, timedelta
import logging
from tqdm import tqdm

# Configure logging - send all messages to file, only errors/warnings to console to avoid interfering with progress bar
logging.basicConfig(
    level=logging.WARNING,  # Set basic level to WARNING to reduce console output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log', encoding='utf-8'),  # Log to file with UTF-8 encoding
    ]
)
logger = logging.getLogger(__name__)

# Add console handler for ERROR and CRITICAL messages only
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Only show errors and critical messages on console
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def sanitize_filename(name):
    # Replace common problematic whitespace
    name = name.replace('\xa0', ' ').strip()
    # Replace invalid characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Optional: collapse multiple underscores/spaces
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing dots or spaces (to be extra safe)
    name = name.strip('. ')
    name = name.replace(" ", "_").replace("\r", '_').replace("\n", '_')
    # Fallback if empty
    if not name:
        name = "unnamed"
    return name

def generate_date_strings(start_str, end_str, fmt="%d.%m.%Y"):
    """
    Generate a list of date strings between start and end dates (inclusive).
    
    Args:
        start_str (str): Start date in 'DD.MM.YYYY' format.
        end_str (str): End date in 'DD.MM.YYYY' format.
        fmt (str): Date format (default: '%d.%m.%Y').

    Returns:
        List[str]: List of date strings in specified format.
    """
    start = datetime.strptime(start_str, fmt)
    end = datetime.strptime(end_str, fmt)
    
    if start > end:
        raise ValueError("Start date must be on or before end date.")
    
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.strftime(fmt))
        current += timedelta(days=1)
    
    return date_list


def build_belta_url(**kwargs):
    params = {
        "query": kwargs.get("query", ""),
        "phrase": kwargs.get("phrase", ""),
        "any_of_words": kwargs.get("any_of_words", ""),
        "none_of_words": kwargs.get("none_of_words", ""),
        "group": kwargs.get("group", 0),
        "period": "period" if (kwargs.get("from_day") or kwargs.get("to_day")) else "",
        "from_day": kwargs.get("from_day", ""),
        "to_day": kwargs.get("to_day", ""),
        "sort_by": kwargs.get("sort_by", "desc")
    }
    params = {k: v for k, v in params.items() if v != ""}
    return "https://belta.by/search/getExtendedResults/?" + urlencode(params)



def get_pages_links(search_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        pages_container = soup.find('div', class_='pages_inner')
        page_links = []
        if pages_container:
            links_tags = pages_container.find_all('a')
            # logger.debug(pages_container)
            for item in links_tags:
                page_links.append("http://belta.by" + str(item['href']))
        
        # for item in links_container:
        #     a_tag = item.find('a', href=True)
        #     if a_tag:
        #         links_extracted.append(a_tag['href'])
        
        # logger.debug(*page_links, sep="\n")
        # Removed logging to prevent interference with progress bar
        return page_links
        # logger.debug(type(links), links, sep="\n")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []
    

def fetch_all_article_links(page_urls, max_workers=10):
    """
    Fetch article links from multiple pages in parallel.
    
    Args:
        page_urls (list): List of page URLs to scrape.
        max_workers (int): Max number of concurrent threads.
        save_html (bool): Whether to save raw HTML files.
    
    Returns:
        list: Combined list of all article URLs (with duplicates).
    """
    all_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(get_article_links, url): url 
            for url in page_urls
        }

        # Collect results
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                links = future.result()
                all_links.extend(links)
            except Exception as e:
                logger.error(f"Unhandled exception for {url}: {e}")

    logger.info(f"Total article links collected: {len(all_links)}")
    return all_links
    
    
def get_article_links(page_url):
    # logger.debug(f"⚠️ Getting {page_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles_links = set()
        links = soup.find_all('a', class_="rubric_item_title", href=True)
        for link in links:
            if link:
                articles_links.add(link['href'])
        # Removed logging to prevent interference with progress bar
        return list(articles_links)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []



def download_image(img_url, base_url, save_dir="images"):
    full_url = urljoin(base_url, img_url)
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        img_data = requests.get(full_url, timeout=10).content
        img_name = str(uuid.uuid4()) + os.path.splitext(urlparse(full_url).path or ".jpg")[1]
        img_path = os.path.join(save_dir, img_name)
        with open(img_path, "wb") as f:
            f.write(img_data)
        return os.path.join(save_dir, img_name)
    except Exception as e:
        logger.error(f"Failed to download {img_url}: {e}")
        return None

def html_to_markdown_with_local_images(html_str: str, base_url: str, md_img_dir: str = "images") -> str:
    os.makedirs(md_img_dir, exist_ok=True)
    # Parse the HTML string
    soup = BeautifulSoup(html_str, 'html.parser')
    
    # Download and replace images
    for img in soup.find_all('img'):
        src = str(img.get('src'))
        if not src:
            continue
        
        full_url = urljoin(base_url, src.strip())
        if not full_url.startswith(('http://', 'https://')):
            continue  # skip invalid URLs

        try:
            img_data = requests.get(full_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).content
            os.makedirs(md_img_dir, exist_ok=True)
            
            ext = os.path.splitext(full_url.split('?')[0].split('/')[-1])[1] or '.jpg'
            filename = f"{uuid.uuid4().hex}{ext}"
            img_path = os.path.join(md_img_dir, filename)
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            # Replace src with relative path
            img['src'] = os.path.join(md_img_dir, filename)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to download image {full_url}: {e}")

    # Convert to Markdown
    return md(str(soup), heading_style="ATX")



def save_page_content(url, folder):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # with open("page.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)
        title = soup.find('title')
        title = sanitize_filename(str(title.contents[0])) if title else f"no_title_{uuid.uuid4()}"

        # Ensure the title is not too long for OS limitations
        if len(title) > 200:  # Windows has path limitations
            title = title[:200]

        content = soup.find('div', class_="text_block")
        if content:
            mark_down_content = md(str(content), heading_style="ATX")

            # Create the file path safely
            file_path = os.path.join(folder, f"{title}.md")

            # Handle potential file name conflicts by appending a number
            counter = 1
            original_file_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_file_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(mark_down_content)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []
    except OSError as e:
        logger.error(f"OS error saving file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in save_page_content: {e}")
        return []




def download_all_from_period(from_day="01.12.2024", to_day="01.12.2024", worker_count=10, worker_timeout=0.0):
    url = build_belta_url(from_day=from_day, to_day=to_day)
    logger.debug(f"Processing {from_day}")
    logger.debug(f"Using URL {url}")

    pages = get_pages_links(url)
    total_links = []

    # Extract year from from_day to create year directory
    date_parts = from_day.split('.')
    year = date_parts[2] if len(date_parts) == 3 else "unknown_year"

    # Create data/year directory
    year_dir = f"./data/{year}"
    os.makedirs(year_dir, exist_ok=True)

    # Create date-specific directory (e.g., 10.10.2011)
    date_dir = os.path.join(year_dir, from_day)
    os.makedirs(date_dir, exist_ok=True)

    # total_links = get_article_links(pages[0])
    for page in pages:
        total_links += get_article_links(page)

    logger.debug(f"Total links found: {len(total_links)}")


    def fetch_article(url):
        try:
            save_page_content(url, date_dir)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        time.sleep(worker_timeout)

    # Delegate tasks to N worker threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(fetch_article, url): url for url in total_links}


    

# logger.debug(url)

def process_single_date(date):
    """Wrapper function to process a single date"""
    download_all_from_period(
        from_day=date,
        to_day=date,
        worker_count=3
    )
    return date

start_date = "01.01.2011"
end_date = "01.01.2012"  # Changed to process 5 days for better progress visualization
dates = generate_date_strings(start_date, end_date)

# Process dates in parallel while maintaining progress bar
with ThreadPoolExecutor(max_workers=min(len(dates), 5)) as executor:
    # Submit all tasks
    futures = {executor.submit(process_single_date, date): date for date in dates}

    # Create progress bar and update as tasks complete
    with tqdm(total=len(dates), desc="Processing dates", unit="date") as pbar:
        for future in concurrent.futures.as_completed(futures):
            date = futures[future]
            try:
                result = future.result()
                pbar.update(1)  # Update progress bar when a date is completed
            except Exception as e:
                logger.error(f"Error processing date {date}: {e}")
                pbar.update(1)  # Still update progress even if there's an error
