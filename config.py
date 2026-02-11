import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # HRDC Website
    HRDC_BASE_URL = "https://www.hrdc.mu/index.php/publications/downloads/17-training-grant-system"
    HRDC_PAGINATION_URL = "https://www.hrdc.mu/index.php/training-grant-system/downloads?start="
    
    # Database
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "hrdc_documents")
    DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    
    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(",")
    
    # LangChain
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDINGS_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Paths
    DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
    STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
    
    # Application
    MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS", "100"))
    DOMAIN = os.getenv("DOMAIN", "hrdc.islandai.co")

config = Config()
