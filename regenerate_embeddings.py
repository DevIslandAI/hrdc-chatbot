from chatbot import HRDCChatbot
import psycopg2
from config import config

def regenerate_embeddings():
    print("="*80)
    print("REGENERATING EMBEDDINGS WITH OPENAI")
    print("="*80)
    
    chatbot = HRDCChatbot()
    if not chatbot.connect_db():
        print("Failed to connect to database")
        return

    try:
        cursor = chatbot.db_conn.cursor()
        
        # 1. Clear existing embeddings
        print("\n1. Clearing existing embeddings...")
        cursor.execute("UPDATE document_content SET embedding = NULL;")
        chatbot.db_conn.commit()
        print("✓ Cleared all embeddings")
        
        # 2. Verify count
        cursor.execute("SELECT COUNT(*) FROM document_content WHERE embedding IS NULL;")
        count = cursor.fetchone()[0]
        print(f"✓ Found {count} chunks to process")
        
        # 3. Regenerate
        print("\n2. Regenerating embeddings...")
        chatbot.update_all_embeddings()
        
        print("\n✓ SUCCESS: All embeddings regenerated with OpenAI model")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        chatbot.db_conn.rollback()
    finally:
        chatbot.disconnect_db()

if __name__ == "__main__":
    regenerate_embeddings()
