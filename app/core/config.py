# app/core/config.py - CORRECTED PATHS

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # Project paths - ALL inside app directory
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    EMBEDDINGS_DIR = DATA_DIR / "embeddings"  # Changed: inside data folder
    
    # API settings
    API_V1_PREFIX = "/api"
    PROJECT_NAME = "SHL Assessment Recommender"
    VERSION = "1.0.0"
    
    # LLM settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Model settings
    LLM_MODEL = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Retrieval settings
    TOP_K_RESULTS = 10
    SIMILARITY_THRESHOLD = 0.3
    
    # Conversation settings
    MAX_TURNS = 8
    MAX_HISTORY_MESSAGES = 10
    
    # Catalog paths (all inside app/data)
    RAW_CATALOG_PATH = DATA_DIR / "raw_catalog.json"
    PROCESSED_CATALOG_PATH = DATA_DIR / "processed_catalog.json"
    VECTOR_STORE_PATH = EMBEDDINGS_DIR / "faiss_index"  # Now app/data/embeddings/
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.EMBEDDINGS_DIR.mkdir(exist_ok=True, parents=True)

settings = Settings()
settings.ensure_directories()