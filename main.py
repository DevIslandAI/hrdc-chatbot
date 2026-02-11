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
    
    if not os.path.exists(metadata_path):
        print("\n❌ Error: metadata.json not found!")
        print(f"Expected location: {metadata_path}")
        return
    
    # Count PDF and DOCX files in downloads directory
    files = [f for f in os.listdir(download_dir) if f.endswith(('.pdf', '.docx', '.doc'))]
    print(f"\n✓ Found {len(files)} document files in {download_dir}")
    
    if len(files) == 0:
        print("\n⚠️  WARNING: No PDF or DOCX files found!")
        print("\nPlease manually download the documents:")
        print("1. Open downloads/metadata.json")
        print("2. For each document, visit the download_url")
        print("3. Save the files to the downloads/ folder")
        print("4. Run this script again")
        return
    
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
