import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
from config import config

class HRDCScraper:
    """Scraper for HRDC Training Grant System documents"""
    
    def __init__(self):
        self.base_url = config.HRDC_BASE_URL
        self.download_dir = config.DOWNLOAD_DIR
        self.documents = []
        
        # Browser-like headers to avoid 403 Forbidden
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
    
    def extract_date_from_tooltip(self, tooltip_html):
        """Extract date from Bootstrap tooltip HTML"""
        if not tooltip_html:
            return None
        
        # Pattern: Date:</div><div class='pd-fl-m pd-col2'>25 April 2024</div>
        pattern = r"Date:</div><div class='pd-fl-m pd-col2'>(.*?)</div>"
        match = re.search(pattern, tooltip_html)
        
        if match:
            return match.group(1).strip()
        return None
    
    def get_file_extension(self, url, title):
        """Determine file extension from URL or title"""
        # Check URL first
        if '.pdf' in url.lower():
            return 'pdf'
        elif '.docx' in url.lower():
            return 'docx'
        elif '.doc' in url.lower():
            return 'doc'
        elif '.png' in url.lower() or '.jpg' in url.lower() or '.jpeg' in url.lower():
            return 'image'
        
        # Check title
        if '.pdf' in title.lower():
            return 'pdf'
        elif '.docx' in title.lower():
            return 'docx'
        elif '.doc' in title.lower():
            return 'doc'
        
        # Default to pdf (most common on the site)
        return 'pdf'
    
    def scrape_page(self, page_number=1):
        """Scrape a single page of documents"""
        if page_number == 1:
            url = self.base_url
        else:
            # Page 2 starts at index 20
            start_index = (page_number - 1) * 20
            url = f"{config.HRDC_PAGINATION_URL}{start_index}"
        
        print(f"Scraping page {page_number}: {url}")
        
        try:
            # Create session with retries
            session = requests.Session()
            session.headers.update(self.headers)
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            page_documents = []
            
            # Find all download buttons
            download_buttons = soup.find_all('a', class_='btn-success')
            
            for download_btn in download_buttons:
                try:
                    # Get download URL
                    download_url = download_btn.get('href')
                    if not download_url:
                        continue
                    
                    # Make absolute URL
                    download_url = urljoin(url, download_url)
                    
                    # Find the corresponding details button (previous sibling)
                    parent = download_btn.find_parent()
                    details_btn = parent.find('a', class_='btn-info') if parent else None
                    
                    # Extract date from details button
                    date = None
                    if details_btn:
                        tooltip = details_btn.get('data-bs-original-title')
                        date = self.extract_date_from_tooltip(tooltip)
                    
                    # Find document title (usually in a link or text before the buttons)
                    title_element = None
                    row = download_btn.find_parent()
                    while row and not title_element:
                        title_element = row.find('a', href=lambda x: x and ('pdf' in x.lower() or 'doc' in x.lower()))
                        if not title_element:
                            # Try to find any text content
                            text_content = row.get_text(strip=True)
                            if text_content and text_content not in ['Details', 'Download']:
                                title_element = text_content
                                break
                        row = row.find_parent()
                    
                    title = title_element.get_text(strip=True) if hasattr(title_element, 'get_text') else str(title_element)
                    
                    # Clean up title
                    title = title.replace('Details', '').replace('Download', '').strip()
                    
                    # Get file extension
                    file_ext = self.get_file_extension(download_url, title)
                    
                    document = {
                        'title': title,
                        'download_url': download_url,
                        'date': date,
                        'file_type': file_ext,
                        'page': page_number
                    }
                    
                    page_documents.append(document)
                    
                except Exception as e:
                    print(f"Error processing document: {e}")
                    continue
            
            return page_documents
            
        except Exception as e:
            print(f"Error scraping page {page_number}: {e}")
            return []
    
    def scrape_all_documents(self):
        """Scrape all documents from both pages"""
        print("Starting HRDC document scraping...")
        
        # Scrape page 1 (documents 1-20)
        page1_docs = self.scrape_page(1)
        print(f"Found {len(page1_docs)} documents on page 1")
        
        # Scrape page 2 (documents 21-31)
        page2_docs = self.scrape_page(2)
        print(f"Found {len(page2_docs)} documents on page 2")
        
        # Combine all documents
        self.documents = page1_docs + page2_docs
        print(f"\nTotal documents found: {len(self.documents)}")
        
        # Group by date
        self.group_by_date()
        
        return self.documents
    
    def group_by_date(self):
        """Group and display documents by date"""
        date_groups = {}
        for doc in self.documents:
            date = doc.get('date', 'Unknown')
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(doc)
        
        print("\n=== Documents grouped by date ===")
        for date, docs in sorted(date_groups.items()):
            print(f"{date}: {len(docs)} documents")
    
    def download_document(self, document, index):
        """Download a single document"""
        try:
            url = document['download_url']
            file_ext = document['file_type']
            
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', document['title'])
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            filename = f"{index:03d}_{safe_title[:50]}.{file_ext}"
            filepath = os.path.join(self.download_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                print(f"Skipping (already exists): {filename}")
                document['file_path'] = filepath
                return True
            
            # Download file with headers
            session = requests.Session()
            session.headers.update(self.headers)
            response = session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            document['file_path'] = filepath
            print(f"Downloaded: {filename}")
            return True
            
        except Exception as e:
            print(f"Error downloading {document['title']}: {e}")
            document['file_path'] = None
            return False
    
    def download_all_documents(self):
        """Download all scraped documents"""
        if not self.documents:
            print("No documents to download. Run scrape_all_documents() first.")
            return
        
        print(f"\nDownloading {len(self.documents)} documents...")
        
        successful = 0
        failed = 0
        
        for index, doc in enumerate(tqdm(self.documents, desc="Downloading"), start=1):
            if self.download_document(doc, index):
                successful += 1
            else:
                failed += 1
        
        print(f"\nDownload complete: {successful} successful, {failed} failed")
    
    def save_metadata(self, filename='metadata.json'):
        """Save document metadata to JSON file"""
        filepath = os.path.join(self.download_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
        
        print(f"Metadata saved to: {filepath}")

def main():
    """Main function to run the scraper"""
    scraper = HRDCScraper()
    
    # Scrape all documents
    documents = scraper.scrape_all_documents()
    
    # Download all documents
    scraper.download_all_documents()
    
    # Save metadata
    scraper.save_metadata()
    
    print("\n=== Scraping complete ===")
    print(f"Total documents: {len(documents)}")
    print(f"Documents saved to: {config.DOWNLOAD_DIR}")

if __name__ == "__main__":
    main()
