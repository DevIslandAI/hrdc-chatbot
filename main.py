#!/usr/bin/env python3
"""
Main pipeline to run the complete HRDC document processing and upload
"""
import os
import sys
from document_processor import DocumentProcessor
from database import DatabaseManager, upload_processed_documents
from chatbot import HRDCChatbot
from config import config

def main():
    """Main execution pipeline"""
    
    print("=" * 80)
    print("HRDC Document Processing Pipeline")
    print("=" * 80)
    
    # Check if downloads directory has files
    download_dir = config.DOWNLOAD_DIR
    metadata_path = os.path.join(download_dir, 'metadata.json')
    
    # Auto-run scraper if metadata.json is missing
    if not os.path.exists(metadata_path):
        print("\n⚠️  metadata.json not found! Starting scraper to download documents...")
        print("=" * 80)
        print("STEP 0: Scraping and Downloading Documents")
        print("=" * 80)
        
        from scraper import HRDCScraper
        scraper = HRDCScraper()
        scraper.scrape_all_documents()
        scraper.download_all_documents()
        scraper.save_metadata()
        
        print("\n✅ Scraping complete. Proceeding to processing...")
    
    # Double check that files now exist
    if not os.path.exists(metadata_path):
        print("\n❌ Error: Scraper failed to generate metadata.json!")
        return

    # Count PDF and DOCX files in downloads directory
    files = [f for f in os.listdir(download_dir) if f.endswith(('.pdf', '.docx', '.doc'))]
    print(f"\n✓ Found {len(files)} document files in {download_dir}")
    
    # Step 1: Process documents
    print("\n" + "=" * 80)
    print("STEP 1: Processing Documents")
    print("=" * 80)
    
    processor = DocumentProcessor()
    processor.load_metadata()
    processor.process_all_documents()
    processor.print_statistics()
    
    processed_path = processor.save_processed_data()
    
    # Step 2: Upload to database
    print("\n" + "=" * 80)
    print("STEP 2: Uploading to PostgreSQL Database")
    print("=" * 80)
    
    success = upload_processed_documents(processed_path)
    
    if not success:
        print("\n❌ Database upload failed! Check your connection settings in .env")
        return
    
    # Step 3: Generate embeddings
    print("\n" + "=" * 80)
    print("STEP 3: Generating Embeddings for ChatBot")
    print("=" * 80)
    
    try:
        chatbot = HRDCChatbot()
        chatbot.connect_db()
        chatbot.update_all_embeddings()
        chatbot.disconnect_db()
    except Exception as e:
        print(f"\n❌ Error generating embeddings: {e}")
        print("You can generate embeddings later by running: python chatbot.py")
    
    # Success!
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 80)
    print("\nAll documents have been processed and uploaded to the database.")
    print("\nNext steps:")
    print("1. Run 'python app.py' to start the Flask web application")
    print("2. Access the chatbot at http://localhost:5000")
    print("3. Deploy to hrdc.islandai.co when ready")
    
if __name__ == "__main__":
    main()
