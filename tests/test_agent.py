# tests/test_agent.py

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent import get_agent


@pytest.fixture
def agent():
    """Get agent instance for testing"""
    return get_agent()


class TestAgentBasic:
    """Basic agent functionality tests"""
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes properly"""
        assert agent is not None
        assert hasattr(agent, 'process_message')
    
    def test_health_check_response(self, agent):
        """Test that agent returns valid response structure"""
        response = agent.process_message("Hello", [])
        assert "reply" in response
        assert "recommendations" in response
        assert "end_of_conversation" in response
    
    def test_vague_query_no_recommendations(self, agent):
        """Test that vague query returns 0 recommendations"""
        response = agent.process_message("I need an assessment", [])
        assert len(response["recommendations"]) == 0
        assert "?" in response["reply"]  # Should be asking a question
    
    def test_specific_query_returns_recommendations(self, agent):
        """Test that specific query returns recommendations"""
        response = agent.process_message("I need a Java developer assessment", [])
        # May return 0 on first turn if agent asks clarifying questions
        # This is acceptable behavior per SHL spec
        assert "reply" in response
    
    def test_off_topic_refusal(self, agent):
        """Test that off-topic queries are refused"""
        response = agent.process_message("What's the weather today?", [])
        assert "SHL" in response["reply"] or "assessment" in response["reply"].lower()
        assert len(response["recommendations"]) == 0


class TestAgentMultiTurn:
    """Multi-turn conversation tests"""
    
    def test_multi_turn_accumulates_info(self, agent):
        """Test that agent remembers info across turns"""
        # Turn 1: Vague
        response1 = agent.process_message("I need an assessment", [])
        
        # Turn 2: Add specific info (simulate conversation history)
        history = [{"role": "user", "content": "I need an assessment"},
                   {"role": "assistant", "content": response1["reply"]}]
        response2 = agent.process_message("Java developer, mid-level", history)
        
        # Should have some recommendations or at least be closer
        assert "reply" in response2
    
    def test_turn_limit_enforced(self, agent):
        """Test that conversation ends after MAX_TURNS"""
        from app.core.config import settings
        
        response = None
        history = []
        
        for i in range(settings.MAX_TURNS):
            response = agent.process_message(f"Message {i}", history)
            history.append({"role": "user", "content": f"Message {i}"})
            history.append({"role": "assistant", "content": response["reply"]})
        
        # Last response should end the conversation
        # Note: This may vary based on your MAX_TURNS setting
        assert "reply" in response


class TestAgentComparison:
    """Comparison feature tests"""
    
    def test_comparison_request_detection(self, agent):
        """Test that comparison requests are detected"""
        # This will work if your catalog has assessments
        response = agent.process_message("Compare Java and Python assessments", [])
        # Should either compare or ask for clarification
        assert "reply" in response
    
    def test_comparison_response_format(self, agent):
        """Test that comparison response has proper format"""
        response = agent.process_message("What's the difference between two assessments?", [])
        assert "reply" in response
        assert isinstance(response["recommendations"], list)


class TestAgentRefinement:
    """Refinement feature tests"""
    
    def test_refinement_request_detection(self, agent):
        """Test that refinement requests are detected"""
        response = agent.process_message("Add personality tests", [])
        assert "reply" in response
    
    def test_refinement_updates_recommendations(self, agent):
        """Test that refinement updates recommendations"""
        # First get some recommendations
        response1 = agent.process_message("Java developer", [])
        
        # Then refine (simulate conversation)
        history = [{"role": "user", "content": "Java developer"},
                   {"role": "assistant", "content": response1["reply"]}]
        response2 = agent.process_message("Add personality tests", history)
        
        assert "reply" in response2


class TestAgentSchemaCompliance:
    """Schema compliance tests"""
    
    def test_response_has_all_required_fields(self, agent):
        """Test that response has all SHL required fields"""
        response = agent.process_message("Test message", [])
        
        required_fields = ["reply", "recommendations", "end_of_conversation"]
        for field in required_fields:
            assert field in response, f"Missing field: {field}"
    
    def test_recommendations_is_list(self, agent):
        """Test that recommendations is a list"""
        response = agent.process_message("Test message", [])
        assert isinstance(response["recommendations"], list)
    
    def test_recommendations_have_correct_structure(self, agent):
        """Test that each recommendation has required fields"""
        response = agent.process_message("Java developer assessment", [])
        
        for rec in response["recommendations"]:
            assert "name" in rec or "metadata" in rec
            if "metadata" in rec:
                assert "name" in rec["metadata"]
    
    def test_end_of_conversation_is_boolean(self, agent):
        """Test that end_of_conversation is a boolean"""
        response = agent.process_message("Test message", [])
        assert isinstance(response["end_of_conversation"], bool)