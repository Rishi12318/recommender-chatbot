from typing import List, Dict
import uuid

def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())

def format_response(data: Dict) -> Dict:
    """Format response data"""
    return {
        "status": "success",
        "data": data,
        "timestamp": None
    }

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text"""
    return text.lower().split()
