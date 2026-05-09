from typing import Dict, List, Optional
from datetime import datetime
import uuid

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}
    
    def create_session(self) -> str:
        """Create new conversation session"""
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "recommendations": []
        }
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add message to conversation"""
        if session_id not in self.conversations:
            return False
        
        self.conversations[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get conversation session"""
        return self.conversations.get(session_id)
    
    def add_recommendation(self, session_id: str, recommendation: Dict) -> bool:
        """Add recommendation to session"""
        if session_id not in self.conversations:
            return False
        
        self.conversations[session_id]["recommendations"].append(recommendation)
        return True
