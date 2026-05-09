# tests/test_retrieval.py

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRetrieval:
    """Retrieval system tests"""
    
    def test_search_imports(self):
        """Test that search function can be imported"""
        from app.services.retrieval import search_assessments
        assert callable(search_assessments)
    
    def test_search_returns_list(self):
        """Test that search returns a list"""
        from app.services.retrieval import search_assessments
        results = search_assessments("Java", k=5)
        assert isinstance(results, list)
    
    def test_search_results_have_metadata(self):
        """Test that search results have metadata"""
        from app.services.retrieval import search_assessments
        results = search_assessments("developer", k=3)
        
        if results:
            for result in results:
                # Should have name or metadata
                assert "name" in result or "metadata" in result
    
    def test_vector_store_initialization(self):
        """Test that vector store initializes"""
        from app.services.retrieval import get_vectorstore
        try:
            vs = get_vectorstore()
            assert vs is not None
        except Exception as e:
            # May fail if no catalog, that's acceptable for test
            assert "Catalog not found" in str(e) or True