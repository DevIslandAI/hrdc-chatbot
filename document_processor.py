import os
import json
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
from typing import List, Dict
from config import config

class DocumentProcessor:
    """Process and extract text from downloaded documents"""
    
    def __init__(self, download_dir=None):
        self.download_dir = download_dir or config.DOWNLOAD_DIR
        self.metadata_path = os.path.join(self.download_dir, 'metadata.json')
        self.documents = []
        self.processed_data = []
    
    def load_metadata(self):
        """Load document metadata from JSON file"""
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        
        print(f"Loaded metadata for {len(self.documents)} documents")
        return self.documents
    
    def extract_text_from_pdf(self, filepath):
        """Extract text from PDF file using pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF {filepath}: {e}")
            return ""
    
    def extract_text_from_docx(self, filepath):
        """Extract text from Word document"""
        try:
            doc = Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from DOCX {filepath}: {e}")
            return ""
    
    def extract_text_from_image(self, filepath):
        """Extract text from image using OCR"""
        try:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from image {filepath}: {e}")
            return ""
    
    def extract_text(self, filepath, file_type):
        """Extract text based on file type"""
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return ""
        
        if file_type == 'pdf':
            return self.extract_text_from_pdf(filepath)
        elif file_type in ['docx', 'doc']:
            return self.extract_text_from_docx(filepath)
        elif file_type == 'image':
            return self.extract_text_from_image(filepath)
        else:
            print(f"Unknown file type: {file_type}")
            return ""
    
    def chunk_text(self, text, chunk_size=None, overlap=None):
        """Split text into overlapping chunks for better context"""
        chunk_size = chunk_size or config.CHUNK_SIZE
        overlap = overlap or config.CHUNK_OVERLAP
        
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence or paragraph boundaries
            if end < text_length:
                # Look for paragraph break
                last_para = chunk.rfind('\n\n')
                if last_para > chunk_size * 0.5:  # At least 50% through
                    end = start + last_para
                    chunk = text[start:end]
                else:
                    # Look for sentence break
                    last_period = max(chunk.rfind('. '), chunk.rfind('.\n'))
                    if last_period > chunk_size * 0.5:
                        end = start + last_period + 1
                        chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def process_document(self, document):
        """Process a single document: extract text and chunk it"""
        filepath = document.get('file_path')
        if not filepath or not os.path.exists(filepath):
            print(f"Skipping document (file not found): {document.get('title', 'Unknown')}")
            return None
        
        print(f"Processing: {document['title']}")
        
        # Extract text
        text = self.extract_text(filepath, document['file_type'])
        
        if not text:
            print(f"  ⚠️  No text extracted from {document['title']}")
            return None
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        print(f"  ✓ Extracted {len(text)} characters, created {len(chunks)} chunks")
        
        return {
            'document': document,
            'full_text': text,
            'chunks': chunks,
            'num_chunks': len(chunks)
        }
    
    def process_all_documents(self):
        """Process all documents from metadata"""
        if not self.documents:
            self.load_metadata()
        
        print(f"\nProcessing {len(self.documents)} documents...")
        
        successful = 0
        failed = 0
        
        for doc in self.documents:
            result = self.process_document(doc)
            if result:
                self.processed_data.append(result)
                successful += 1
            else:
                failed += 1
        
        print(f"\nProcessing complete: {successful} successful, {failed} failed")
        return self.processed_data
    
    def save_processed_data(self, filename='processed_documents.json'):
        """Save processed document data to JSON file"""
        filepath = os.path.join(self.download_dir, filename)
        
        # Prepare data for JSON (remove full_text to save space, keep chunks)
        json_data = []
        for item in self.processed_data:
            json_data.append({
                'document': item['document'],
                'num_chunks': item['num_chunks'],
                'chunks': item['chunks']
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"Processed data saved to: {filepath}")
        return filepath
    
    def get_statistics(self):
        """Get processing statistics"""
        if not self.processed_data:
            return None
        
        total_docs = len(self.processed_data)
        total_chunks = sum(item['num_chunks'] for item in self.processed_data)
        
        # Group by date
        date_stats = {}
        for item in self.processed_data:
            date = item['document'].get('date', 'Unknown')
            if date not in date_stats:
                date_stats[date] = {'docs': 0, 'chunks': 0}
            date_stats[date]['docs'] += 1
            date_stats[date]['chunks'] += item['num_chunks']
        
        stats = {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'avg_chunks_per_doc': total_chunks / total_docs if total_docs > 0 else 0,
            'by_date': date_stats
        }
        
        return stats
    
    def print_statistics(self):
        """Print processing statistics"""
        stats = self.get_statistics()
        if not stats:
            print("No statistics available")
            return
        
        print("\n=== Processing Statistics ===")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total text chunks: {stats['total_chunks']}")
        print(f"Average chunks per document: {stats['avg_chunks_per_doc']:.1f}")
        
        print("\nBy date:")
        for date, data in sorted(stats['by_date'].items()):
            print(f"  {date}: {data['docs']} docs, {data['chunks']} chunks")

def main():
    """Main function to run the document processor"""
    processor = DocumentProcessor()
    
    # Load metadata
    processor.load_metadata()
    
    # Process all documents
    processor.process_all_documents()
    
    # Save processed data
    processor.save_processed_data()
    
    # Print statistics
    processor.print_statistics()

if __name__ == "__main__":
    main()
