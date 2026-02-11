#!/usr/bin/env python3
"""
Update metadata.json with actual file paths from downloads directory
"""
import os
import json
import glob

def update_metadata_with_actual_files():
    """Match downloaded files to metadata entries"""
    
    metadata_path = 'downloads/metadata.json'
    download_dir = 'downloads'
    
    # Load metadata
    with open(metadata_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    # Get all PDF and DOCX files
    all_files = glob.glob(os.path.join(download_dir, '*.pdf'))
    all_files += glob.glob(os.path.join(download_dir, '*.docx'))
    all_files += glob.glob(os.path.join(download_dir, '*.doc'))
    
    print(f"Found {len(all_files)} files in {download_dir}")
    print(f"Have {len(documents)} metadata entries")
    
    # Create mapping based on filename matching
    updated = 0
    for doc in documents:
        # Try to find a matching file
        title_words = doc['title'].lower().split()
        best_match = None
        best_score = 0
        
        for filepath in all_files:
            filename = os.path.basename(filepath).lower()
            # Count how many title words appear in filename
            score = sum(1 for word in title_words if len(word) > 3 and word in filename)
            if score > best_score:
                best_score = score
                best_match = filepath
        
        if best_match and best_score > 0:
            doc['file_path'] = os.path.abspath(best_match)
            doc['file_type'] = best_match.split('.')[-1]
            updated += 1
            print(f"✓ Matched: {doc['title'][:50]} -> {os.path.basename(best_match)}")
        else:
            print(f"✗ No match: {doc['title'][:50]}")
    
    # Save updated metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Updated {updated}/{len(documents)} document file paths")
    return updated

if __name__ == "__main__":
    update_metadata_with_actual_files()
