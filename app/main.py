# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import router
from app.services.retrieval import get_vectorstore
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown events"""
    print("[START] Starting up SHL Assessment Recommender...")
    
    # Initialize vector store on startup
    try:
        get_vectorstore()
        print("[OK] Vector store initialized successfully")
    except Exception as e:
        print(f"[!] Vector store initialization warning: {e}")
        print("   Will retry on first search request")
    
    yield
    
    print("[STOP] Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SHL Assessment Recommender",
    description="AI Agent for SHL Assessment Recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router, prefix="/api", tags=["chat"])


@app.get("/")
def root():
    return {
        "service": "SHL Assessment Recommender",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "chat": "/api/chat",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}