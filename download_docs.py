#!/usr/bin/env python3
"""
Download documents from metadata scraped by browser
"""
import os
import json
import requests
from tqdm import tqdm
import re

def download_documents(metadata_path='downloads/metadata.json', download_dir='downloads'):
    """Download all documents from the metadata file"""
    
    # Browser headers to avoid blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.hrdc.mu/'
    }
    
    # Load metadata
    with open(metadata_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"Found {len(documents)} documents to download\n")
    
    # Create download directory
    os.makedirs(download_dir, exist_ok=True)
    
    successful = 0
    failed = 0
    
    for idx, doc in enumerate(tqdm(documents, desc="Downloading"), start=1):
        try:
            url = doc['download_url']
            file_ext = doc.get('file_type', 'pdf')
            
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', doc['title'])
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            filename = f"{idx:03d}_{safe_title[:50]}.{file_ext}"
            filepath = os.path.join(download_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                doc['file_path'] = filepath
                successful += 1
                continue
            
            # Download file
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            doc['file_path'] = filepath
            successful += 1
            
        except Exception as e:
            print(f" \nError downloading {doc['title']}: {e}")
            doc['file_path'] = None
            failed += 1
    
    print(f"\nDownload complete: {successful} successful, {failed} failed")
    
    # Save updated metadata with file paths
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    return successful, failed

if __name__ == "__main__":
    download_documents()
