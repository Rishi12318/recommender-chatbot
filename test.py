# app/services/retrieval.py (modified version)

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Search result with metadata attribute"""
    metadata: Dict[str, Any]
    score: float
    
    def __repr__(self):
        return f"SearchResult(metadata={self.metadata.get('name', 'N/A')}, score={self.score})"


class SimpleRetriever:
    """Simple retriever that returns SearchResult objects"""
    
    def __init__(self, catalog_path: str = "app/data/processed_catalog.json"):
        self.catalog_path = Path(catalog_path)
        self.assessments = []
        self._load_catalog()
    
    def _load_catalog(self):
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found at {self.catalog_path}")
        
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self.assessments = json.load(f)
        
        print(f"✅ Loaded {len(self.assessments)} assessments")
    
    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """Search and return SearchResult objects"""
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score each assessment
        scored_results = []
        
        for assessment in self.assessments:
            score = 0
            
            # Search in name
            name = assessment.get("name", "").lower()
            for word in query_words:
                if word in name:
                    score += 10
            
            # Search in description
            desc = assessment.get("description", "").lower()
            for word in query_words:
                if word in desc:
                    score += 3
            
            # Search in test types
            test_types = " ".join(assessment.get("test_types", [])).lower()
            for word in query_words:
                if word in test_types:
                    score += 5
            
            # Specific keyword boosts
            if "java" in query_lower:
                if "java" in name or "java" in desc:
                    score += 8
            if "backend" in query_lower:
                if "backend" in desc or "server" in desc:
                    score += 5
            
            if score > 0:
                scored_results.append((score, assessment))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return SearchResult objects
        return [SearchResult(metadata=assessment, score=score) 
                for score, assessment in scored_results[:k]]


# Singleton instance
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = SimpleRetriever()
    return _retriever

def search_assessments(query: str, k: int = 10) -> List[SearchResult]:
    """Search assessments and return SearchResult objects"""
    retriever = get_retriever()
    return retriever.search(query, k)


# For testing
if __name__ == "__main__":
    results = search_assessments("Java backend developer", k=5)
    
    for r in results:
        print(f"\n{'='*50}")
        print(f"NAME: {r.metadata['name']}")
        print(f"SCORE: {r.score}")
        print(f"TEST TYPES: {r.metadata['test_types']}")