# tests/test_api.py

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


class TestAPI:
    """API endpoint tests"""
    
    def test_health_endpoint(self, client):
        """Test GET /api/health"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_chat_endpoint_exists(self, client):
        """Test POST /api/chat exists"""
        response = client.post("/api/chat", json={"messages": []})
        # Should return 400 for invalid request, not 404
        assert response.status_code != 404
    
    def test_chat_empty_messages(self, client):
        """Test chat with empty messages"""
        response = client.post("/api/chat", json={"messages": []})
        assert response.status_code == 400
    
    def test_chat_invalid_request(self, client):
        """Test chat with invalid request body"""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422  # Validation error
    
    def test_chat_valid_request(self, client):
        """Test chat with valid request"""
        response = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "Test message"}]
        })
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
    
    def test_chat_with_history(self, client):
        """Test chat with conversation history"""
        response = client.post("/api/chat", json={
            "messages": [
                {"role": "user", "content": "I need an assessment"},
                {"role": "assistant", "content": "What role?"},
                {"role": "user", "content": "Java developer"}
            ]
        })
        assert response.status_code == 200
    
    def test_response_schema_compliance(self, client):
        """Test that response complies with SHL schema"""
        response = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "Java developer"}]
        })
        data = response.json()
        
        # Check required fields
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
        
        # Check types
        assert isinstance(data["reply"], str)
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["end_of_conversation"], bool)
        
        # Check recommendations structure (if any)
        for rec in data["recommendations"]:
            assert "name" in rec
            assert "url" in rec
            assert "test_type" in rec
    
    def test_no_recommendations_on_vague_query(self, client):
        """Test that vague query doesn't return recommendations on turn 1"""
        response = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "I need an assessment"}]
        })
        data = response.json()
        
        # Should have 0 or very few recommendations on turn 1
        assert len(data["recommendations"]) <= 3
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/chat")
        assert "access-control-allow-origin" in response.headers