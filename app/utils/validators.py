from typing import Dict, Any

class ResponseValidator:
    @staticmethod
    def validate_chat_response(response: Dict[str, Any]) -> bool:
        """Validate chat response structure"""
        required_fields = ["response", "session_id"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def validate_recommendation(recommendation: Dict[str, Any]) -> bool:
        """Validate recommendation structure"""
        required_fields = ["id", "name", "score"]
        return all(field in recommendation for field in required_fields)
