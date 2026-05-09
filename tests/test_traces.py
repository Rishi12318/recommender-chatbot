# tests/test_traces.py - CORRECTED

import json
import pytest
from pathlib import Path
from app.services.agent import get_agent


class TestTraces:
    def setup_method(self):
        """Load traces or skip if not available"""
        traces_path = Path("evaluation/conversation_traces")
        
        if not traces_path.exists():
            pytest.skip(f"No traces found at {traces_path}")
        
        trace_files = list(traces_path.glob("*.json"))
        
        if not trace_files:
            pytest.skip("No trace JSON files found")
        
        self.traces = []
        for trace_file in trace_files:
            with open(trace_file, 'r') as f:
                self.traces.append(json.load(f))
    
    def test_traces_loaded(self):
        """Test that traces are loaded"""
        assert len(self.traces) > 0, "No traces loaded. Please add trace files to evaluation/conversation_traces/"
    
    def test_agent_on_traces(self):
        """Test agent on all traces"""
        agent = get_agent()
        
        for trace in self.traces:
            # Run conversation
            response = None
            for turn in trace.get('conversation', []):
                response = agent.process_message(turn['user'], [])
            
            # Verify response has recommendations
            if response and trace.get('expected_assessments'):
                assert response.get('recommendations') is not None