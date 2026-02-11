import psycopg2
from psycopg2.extras import execute_values
import json
from datetime import datetime
from typing import List, Dict
from config import config

class DatabaseManager:
    """Manage PostgreSQL database connection and operations"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=config.DATABASE_HOST,
                database=config.DATABASE_NAME,
                user=config.DATABASE_USER,
                password=config.DATABASE_PASSWORD,
                port=config.DATABASE_PORT
            )
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database: {config.DATABASE_NAME}")
            return True
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed")
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        if not self.conn:
            print("Not connected to database")
            return False
        
        try:
            # Try to enable pgvector extension (optional)
            use_vector = False
            try:
                self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.conn.commit()  # Commit the extension creation
                use_vector = True
                print("✓ Using pgvector extension for embeddings")
            except Exception as e:
                # Rollback the failed transaction before continuing
                self.conn.rollback()
                use_vector = False
                print("⚠ pgvector not available, using JSONB for embeddings")
            
            # Create documents table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(500),
                    filename VARCHAR(255),
                    file_type VARCHAR(50),
                    date DATE,
                    download_url TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create document_content table with conditional embedding type
            if use_vector:
                embedding_col = "embedding vector(384)"
            else:
                embedding_col = "embedding JSONB"
            
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS document_content (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER,
                    content TEXT,
                    {embedding_col},
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_date 
                ON documents(date);
            """)
            
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_document 
                ON document_content(document_id);
            """)
            
            # Create vector index for similarity search (only if pgvector available)
            if use_vector:
                try:
                    self.cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_content_embedding 
                        ON document_content 
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                except Exception as e:
                    # Index creation might fail if not enough data, that's okay
                    print(f"Note: Vector index will be created after adding data")
            
            self.conn.commit()
            print("✓ Database tables created successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            self.conn.rollback()
            return False
    
    def parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str or date_str == 'Unknown':
            return None
        
        try:
            # Try parsing "25 April 2024" format
            return datetime.strptime(date_str, "%d %B %Y").date()
        except:
            try:
                # Try parsing other formats
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                return None
    
    def insert_document(self, document: Dict):
        """Insert a single document into the database"""
        try:
            date_obj = self.parse_date(document.get('date'))
            
            self.cursor.execute("""
                INSERT INTO documents (title, filename, file_type, date, download_url, file_path)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                document.get('title'),
                document.get('file_path', '').split('/')[-1] if document.get('file_path') else None,
                document.get('file_type'),
                date_obj,
                document.get('download_url'),
                document.get('file_path')
            ))
            
            doc_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return doc_id
            
        except Exception as e:
            print(f"Error inserting document: {e}")
            self.conn.rollback()
            return None
    
    def insert_document_chunks(self, document_id: int, chunks: List[str], embeddings: List = None):
        """Insert document chunks into the database"""
        try:
            # Prepare data for batch insert
            if embeddings and len(embeddings) == len(chunks):
                # With embeddings
                data = [
                    (document_id, idx, chunk, embedding)
                    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
                
                execute_values(
                    self.cursor,
                    """
                    INSERT INTO document_content (document_id, chunk_index, content, embedding)
                    VALUES %s
                    """,
                    data
                )
            else:
                # Without embeddings (will be added later)
                data = [
                    (document_id, idx, chunk)
                    for idx, chunk in enumerate(chunks)
                ]
                
                execute_values(
                    self.cursor,
                    """
                    INSERT INTO document_content (document_id, chunk_index, content)
                    VALUES %s
                    """,
                    data
                )
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error inserting chunks: {e}")
            self.conn.rollback()
            return False
    
    def update_embeddings(self, chunk_id: int, embedding: List[float]):
        """Update embedding for a specific chunk"""
        try:
            # Convert to JSON for JSONB compatibility
            import json
            self.cursor.execute("""
                UPDATE document_content
                SET embedding = %s::jsonb
                WHERE id = %s
            """, (json.dumps(embedding), chunk_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            # Try as vector type if JSONB fails
            try:
                self.cursor.execute("""
                    UPDATE document_content
                    SET embedding = %s
                    WHERE id = %s
                """, (embedding, chunk_id))
                self.conn.commit()
                return True
            except:
                print(f"Error updating embedding: {e}")
                self.conn.rollback()
                return False
    
    def get_all_documents(self):
        """Get all documents from database"""
        try:
            self.cursor.execute("SELECT * FROM documents ORDER BY date DESC, id;")
            columns = [desc[0] for desc in self.cursor.description]
            results = self.cursor.fetchall()
            
            documents = []
            for row in results:
                documents.append(dict(zip(columns, row)))
            
            return documents
        except Exception as e:
            print(f"Error fetching documents: {e}")
            return []
    
    def search_documents(self, query: str, limit: int = 5):
        """Search documents using full-text search"""
        try:
            self.cursor.execute("""
                SELECT d.*, dc.content, dc.chunk_index
                FROM documents d
                JOIN document_content dc ON d.id = dc.document_id
                WHERE dc.content ILIKE %s
                ORDER BY d.date DESC
                LIMIT %s;
            """, (f'%{query}%', limit))
            
            columns = [desc[0] for desc in self.cursor.description]
            results = self.cursor.fetchall()
            
            documents = []
            for row in results:
                documents.append(dict(zip(columns, row)))
            
            return documents
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def get_statistics(self):
        """Get database statistics"""
        try:
            # Count documents
            self.cursor.execute("SELECT COUNT(*) FROM documents;")
            doc_count = self.cursor.fetchone()[0]
            
            # Count chunks
            self.cursor.execute("SELECT COUNT(*) FROM document_content;")
            chunk_count = self.cursor.fetchone()[0]
            
            # Count by date
            self.cursor.execute("""
                SELECT date, COUNT(*) as count
                FROM documents
                WHERE date IS NOT NULL
                GROUP BY date
                ORDER BY date;
            """)
            date_stats = self.cursor.fetchall()
            
            return {
                'total_documents': doc_count,
                'total_chunks': chunk_count,
                'by_date': {str(date): count for date, count in date_stats}
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return None

def upload_processed_documents(processed_data_path: str):
    """Upload processed documents to database"""
    db = DatabaseManager()
    
    if not db.connect():
        return False
    
    # Create tables
    db.create_tables()
    
    # Load processed data
    with open(processed_data_path, 'r', encoding='utf-8') as f:
        processed_data = json.load(f)
    
    print(f"\nUploading {len(processed_data)} documents to database...")
    
    successful = 0
    failed = 0
    
    for item in processed_data:
        document = item['document']
        chunks = item['chunks']
        
        # Insert document
        doc_id = db.insert_document(document)
        if not doc_id:
            failed += 1
            continue
        
        # Insert chunks
        if db.insert_document_chunks(doc_id, chunks):
            successful += 1
            print(f"✓ Uploaded: {document['title']} ({len(chunks)} chunks)")
        else:
            failed += 1
            print(f"✗ Failed: {document['title']}")
    
    print(f"\nUpload complete: {successful} successful, {failed} failed")
    
    # Print statistics
    stats = db.get_statistics()
    if stats:
        print("\n=== Database Statistics ===")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Documents by date:")
        for date, count in stats['by_date'].items():
            print(f"  {date}: {count}")
    
    db.disconnect()
    return True

def main():
    """Main function for testing database operations"""
    db = DatabaseManager()
    
    if db.connect():
        db.create_tables()
        stats = db.get_statistics()
        if stats:
            print("\n=== Database Statistics ===")
            print(f"Total documents: {stats['total_documents']}")
            print(f"Total chunks: {stats['total_chunks']}")
        db.disconnect()

if __name__ == "__main__":
    main()
