# app/services/retrieval.py - NO LANGCHAIN VERSION

import json
import re
from pathlib import Path
from typing import List, Dict, Any

from app.core.config import settings

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    ADVANCED_RETRIEVAL_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    faiss = None
    ADVANCED_RETRIEVAL_AVAILABLE = False


class AssessmentVectorStore:
    """Vector store for SHL assessments using FAISS - No LangChain"""
    
    def __init__(
        self, 
        catalog_path: str = None,
        vectorstore_path: str = None,
        embedding_model: str = None
    ):
        self.catalog_path = Path(catalog_path or settings.PROCESSED_CATALOG_PATH)
        self.vectorstore_path = Path(vectorstore_path or settings.VECTOR_STORE_PATH)
        self.embedding_model_name = embedding_model or settings.EMBEDDING_MODEL
        self.model = None
        self.index = None
        self.assessments = []
        self.fallback_mode = not ADVANCED_RETRIEVAL_AVAILABLE
        self._initialize()
    
    def _initialize(self):
        """Initialize embeddings and vector store"""

        if self.fallback_mode:
            self._load_catalog_only()
            print("[!] Advanced retrieval unavailable, using lightweight fallback search")
            return
        
        print(f"[...] Loading embedding model: {self.embedding_model_name}")
        try:
            self.model = SentenceTransformer(self.embedding_model_name)
            print("[OK] Embedding model loaded")
        except Exception as e:
            print(f"[ERR] Failed to load embeddings: {e}")
            raise
        
        # Try to load existing index
        index_path = self.vectorstore_path / "index.faiss"
        metadata_path = self.vectorstore_path / "metadata.json"
        
        if index_path.exists() and metadata_path.exists():
            self._load_index()
        else:
            self._create_index()

    def _load_catalog_only(self):
        """Load catalog without embeddings for fallback search"""
        if not self.catalog_path.exists():
            self.assessments = []
            return

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            self.assessments = json.load(f)
    
    def _create_index(self):
        """Create FAISS index from catalog"""
        
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found at {self.catalog_path}")
        
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            self.assessments = json.load(f)
        
        print(f"📚 Loaded {len(self.assessments)} assessments")
        
        # Create text representations
        texts = []
        for item in self.assessments:
            text = self._format_assessment_text(item)
            texts.append(text)
        
        # Create embeddings
        print("🔨 Creating embeddings...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Save
        self._save_index()
        print(f"[OK] Created FAISS index with {len(self.assessments)} vectors")
    
    def _format_assessment_text(self, item: Dict) -> str:
        """Format assessment as searchable text"""
        
        test_types = item.get('test_types', [])
        if isinstance(test_types, str):
            test_types = [test_types]
        
        job_levels = item.get('job_levels', [])
        if isinstance(job_levels, str):
            job_levels = [job_levels]
        
        languages = item.get('languages', [])
        if isinstance(languages, str):
            languages = [languages]
        
        text = f"""
Assessment Name: {item.get('name', '')}
Description: {item.get('description', '')}
Test Types: {', '.join(test_types) if test_types else 'General'}
Job Levels: {', '.join(job_levels) if job_levels else 'All levels'}
Languages: {', '.join(languages) if languages else 'English'}
Duration: {item.get('duration', 'Not specified')}
Remote Support: {item.get('remote_support', 'Unknown')}
Adaptive: {item.get('adaptive', 'Unknown')}
"""
        return text.strip()
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(self.vectorstore_path / "index.faiss"))
        
        with open(self.vectorstore_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.assessments, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved index to {self.vectorstore_path}")
    
    def _load_index(self):
        """Load existing FAISS index"""
        print(f"📂 Loading existing index from {self.vectorstore_path}")
        
        self.index = faiss.read_index(str(self.vectorstore_path / "index.faiss"))
        
        with open(self.vectorstore_path / "metadata.json", "r", encoding="utf-8") as f:
            self.assessments = json.load(f)
        
        print(f"[OK] Loaded index with {len(self.assessments)} assessments")
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar assessments"""
        
        if self.fallback_mode or self.index is None:
            return self._fallback_search(query, k)
        
        # Create query embedding
        query_embedding = self.model.encode([query])
        
        # Search
        k = min(k, len(self.assessments))
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.assessments):
                similarity = 1 / (1 + distances[0][i])
                results.append({
                    "metadata": self.assessments[idx],
                    "similarity_score": similarity
                })
        
        return results

    def _fallback_search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Lightweight keyword scoring search used when embeddings are unavailable"""

        if not self.assessments:
            self._load_catalog_only()

        query_lower = query.lower()
        query_words = set(re.findall(r"[a-z0-9]+", query_lower))

        scored_results = []
        for assessment in self.assessments:
            score = 0
            name = assessment.get("name", "").lower()
            description = assessment.get("description", "").lower()
            test_types = " ".join(assessment.get("test_types", [])).lower()

            for word in query_words:
                if word in name:
                    score += 10
                if word in description:
                    score += 3
                if word in test_types:
                    score += 5

            if score > 0:
                scored_results.append((score, assessment))

        scored_results.sort(key=lambda item: item[0], reverse=True)

        return [
            {"metadata": assessment, "similarity_score": float(score)}
            for score, assessment in scored_results[:k]
        ]


# Singleton
_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = AssessmentVectorStore()
    return _vectorstore

def search_assessments(query: str, k: int = 10, return_type: str = "metadata"):
    """Search assessments"""
    vectorstore = get_vectorstore()
    results = vectorstore.search(query, k=k)
    
    if return_type == "metadata":
        return [r["metadata"] for r in results]
    return results


if __name__ == "__main__":
    print("Testing vector store...")
    vs = AssessmentVectorStore()
    results = vs.search("Java developer assessment", k=3)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['metadata'].get('name', 'N/A')}")
        print(f"   Score: {r['similarity_score']:.3f}")