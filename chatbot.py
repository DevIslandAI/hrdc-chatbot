import os
import psycopg2
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import config

class HRDCChatbot:
    """LangChain-based RAG chatbot for HRDC documents"""
    
    def __init__(self):
        self.db_conn = None
        self.openai_client = None
        self.model_name = config.EMBEDDINGS_MODEL
        self._init_openai()
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            print(f"Initializing OpenAI client with model: {self.model_name}")
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            print("✓ OpenAI client initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing OpenAI client: {e}")
            raise
    
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(
                host=config.DATABASE_HOST,
                database=config.DATABASE_NAME,
                user=config.DATABASE_USER,
                password=config.DATABASE_PASSWORD,
                port=config.DATABASE_PORT
            )
            print("✓ Connected to database")
            return True
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            return False
    
    def disconnect_db(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()
            print("Database connection closed")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text using OpenAI"""
        try:
            # Clean text
            text = text.replace("\n", " ")
            response = self.openai_client.embeddings.create(
                input=[text],
                model=self.model_name
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI"""
        try:
            # OpenAI has a limit on batch size, processing in chunks of 20
            all_embeddings = []
            batch_size = 20
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                # Clean batch texts
                clean_batch = [t.replace("\n", " ") for t in batch]
                
                response = self.openai_client.embeddings.create(
                    input=clean_batch,
                    model=self.model_name
                )
                
                # Sort by index to maintain order
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                print(f"  Generated {len(batch_embeddings)} embeddings...")
                
            return all_embeddings
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return []
    
    def update_all_embeddings(self):
        """Generate and update embeddings for all document chunks in the database"""
        if not self.db_conn:
            print("Not connected to database")
            return False
        
        try:
            import json
            cursor = self.db_conn.cursor()
            
            # Get all chunks without embeddings
            cursor.execute("""
                SELECT id, content
                FROM document_content
                WHERE embedding IS NULL
                ORDER BY id;
            """)
            
            chunks = cursor.fetchall()
            
            if not chunks:
                print("No chunks found that need embeddings")
                return True
            
            print(f"\nGenerating embeddings for {len(chunks)} chunks...")
            
            # Extract IDs and texts
            chunk_ids = [chunk[0] for chunk in chunks]
            texts = [chunk[1] for chunk in chunks]
            
            # Generate embeddings in batch
            embeddings = self.generate_embeddings_batch(texts)
            
            if not embeddings:
                return False
            
            # Update database with embeddings
            print("Updating database with embeddings...")
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                # Convert numpy array to list, then to JSON string for JSONB
                embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                cursor.execute("""
                    UPDATE document_content
                    SET embedding = %s::jsonb
                    WHERE id = %s
                """, (json.dumps(embedding_list), chunk_id))
            
            self.db_conn.commit()
            print(f"✓ Successfully updated {len(embeddings)} embeddings")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"✗ Error updating embeddings: {e}")
            self.db_conn.rollback()
            return False
    
    def search_similar_chunks(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for chunks similar to the query using vector similarity"""
        if not self.db_conn:
            print("Not connected to database")
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            cursor = self.db_conn.cursor()
            
            # Check if using pgvector or JSONB
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'document_content' AND column_name = 'embedding';
            """)
            result = cursor.fetchone()
            use_pgvector = result and 'vector' in str(result[1]).lower()
            
            if use_pgvector:
                # Vector similarity search using cosine distance
                cursor.execute("""
                    SELECT 
                        dc.id,
                        dc.content,
                        dc.chunk_index,
                        d.id as document_id,
                        d.title,
                        d.date,
                        d.file_type,
                        d.download_url,
                        1 - (dc.embedding <=> %s::vector) as similarity
                    FROM document_content dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s;
                """, (query_embedding, query_embedding, limit))
            else:
                # JSONB-based similarity search with manual cosine calculation
                # Fetch all embeddings and calculate similarity in Python
                cursor.execute("""
                    SELECT 
                        dc.id,
                        dc.content,
                        dc.chunk_index,
                        d.id as document_id,
                        d.title,
                        d.date,
                        d.file_type,
                        d.download_url,
                        dc.embedding::text
                    FROM document_content dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                    LIMIT 500;
                """)
                
                rows = cursor.fetchall()
                
                # Calculate cosine similarity for each
                import json
                import numpy as np
                
                query_emb = np.array(query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding)
                query_norm = np.linalg.norm(query_emb)
                
                similarities = []
                for row in rows:
                    doc_emb = np.array(json.loads(row[8]))
                    doc_norm = np.linalg.norm(doc_emb)
                    
                    if query_norm > 0 and doc_norm > 0:
                        similarity = np.dot(query_emb, doc_emb) / (query_norm * doc_norm)
                        similarities.append((*row[:8], float(similarity)))
                
                # Sort by similarity and take top N
                similarities.sort(key=lambda x: x[8], reverse=True)
                results = similarities[:limit]
            
            if use_pgvector:
                results = cursor.fetchall()
            
            cursor.close()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'chunk_id': row[0],
                    'content': row[1],
                    'chunk_index': row[2],
                    'document_id': row[3],
                    'title': row[4],
                    'date': str(row[5]) if row[5] else 'Unknown',
                    'file_type': row[6],
                    'download_url': row[7],
                    'similarity': float(row[8]) if len(row) > 8 else 0.0
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching similar chunks: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to keyword search
            return self.search_by_keyword(query, limit)
    
    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Search documents by keyword (fallback method)"""
        if not self.db_conn:
            print("Not connected to database")
            return []
        
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                SELECT 
                    dc.id,
                    dc.content,
                    dc.chunk_index,
                    d.id as document_id,
                    d.title,
                    d.date,
                    d.file_type,
                    d.download_url
                FROM document_content dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.content ILIKE %s
                ORDER BY d.date DESC
                LIMIT %s;
            """, (f'%{keyword}%', limit))
            
            results = cursor.fetchall()
            cursor.close()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'chunk_id': row[0],
                    'content': row[1],
                    'chunk_index': row[2],
                    'document_id': row[3],
                    'title': row[4],
                    'date': str(row[5]) if row[5] else 'Unknown',
                    'file_type': row[6],
                    'download_url': row[7]
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching by keyword: {e}")
            return []
    
    def get_documents_by_date(self, date_str: str = None) -> List[Dict]:
        """Get all documents for a specific date"""
        if not self.db_conn:
            print("Not connected to database")
            return []
        
        try:
            cursor = self.db_conn.cursor()
            
            if date_str:
                cursor.execute("""
                    SELECT id, title, date, file_type, download_url
                    FROM documents
                    WHERE date::text LIKE %s
                    ORDER BY title;
                """, (f'%{date_str}%',))
            else:
                cursor.execute("""
                    SELECT id, title, date, file_type, download_url
                    FROM documents
                    ORDER BY date DESC, title;
                """)
            
            results = cursor.fetchall()
            cursor.close()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'document_id': row[0],
                    'title': row[1],
                    'date': str(row[2]) if row[2] else 'Unknown',
                    'file_type': row[3],
                    'download_url': row[4]
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error getting documents by date: {e}")
            return []
    
    def generate_answer_with_llm(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate a natural language answer using OpenAI Chat Completion"""
        if not context_chunks:
            return "I couldn't find any relevant information in the HRDC documents to answer your question."

        try:
            # Prepare context from retrieved chunks
            context_text = ""
            for i, chunk in enumerate(context_chunks, 1):
                context_text += f"Source {i} (Document: {chunk['title']}, Date: {chunk['date']}):\n{chunk['content']}\n\n"

            # Construct system and user messages
            system_prompt = """You are the HRDC Training Grant Assistant. Your job is to answer user questions ACCURATELY based ONLY on the provided context documents.
            
Rules:
1. Answer the question clearly and concisely.
2. Use the provided context to form your answer. Do not make up information.
3. If the answer is not in the context, say so.
4. Cite your sources by referring to the Document Title or Date when relevant.
5. Format your response with Markdown (bolding key terms, using bullet points for lists).
6. Be professional and helpful."""

            user_prompt = f"""Question: {query}

Context Information:
{context_text}

Please answer the question based on the context above."""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3, # Low temperature for factual accuracy
                max_tokens=1000
            )
            
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating LLM answer: {e}")
            return "I encountered an error while streamlining the answer. Please try again."

    def ask(self, query: str, use_vector_search: bool = True) -> Dict:
        """Main query method - ask a question and get an answer"""
        if not self.db_conn:
            self.connect_db()
        
        # Search for relevant chunks
        if use_vector_search:
            # Increase limit to give LLM more context
            results = self.search_similar_chunks(query, limit=7)
        else:
            results = self.search_by_keyword(query, limit=7)
        
        # Generate RAG response
        response_text = self.generate_answer_with_llm(query, results)
        
        return {
            'query': query,
            'response': response_text,
            'sources': results, # Keep sources for UI display
            'num_sources': len(results)
        }

def main():
    """Test the chatbot"""
    chatbot = HRDCChatbot()
    
    if not chatbot.connect_db():
        print("Failed to connect to database")
        return
    
    # Update embeddings if needed
    print("\nChecking if embeddings need to be updated...")
    chatbot.update_all_embeddings()
    
    # Test queries
    test_queries = [
        "What are the training grant requirements?",
        "attendance sheet",
        "documents from April 2024"
    ]
    
    print("\n=== Testing Chatbot ===\n")
    for query in test_queries:
        print(f"Q: {query}")
        result = chatbot.ask(query)
        print(f"A: {result['response']}\n")
        print(f"Sources found: {result['num_sources']}\n")
        print("-" * 80 + "\n")
    
    chatbot.disconnect_db()

if __name__ == "__main__":
    main()
