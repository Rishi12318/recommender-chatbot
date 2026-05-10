# app/services/agent.py - CLEAN FINAL VERSION

import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from app.core.prompts import SYSTEM_PROMPT
from app.services.llm_client import get_llm_client
from app.services.retrieval import search_assessments
from app.core.config import settings


class AgentState(Enum):
    GATHERING = "gathering"
    SEARCHING = "searching"
    RECOMMENDING = "recommending"
    COMPLETE = "complete"


@dataclass
class ConversationState:
    """Track conversation state"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    extracted_requirements: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    state: AgentState = AgentState.GATHERING
    recommendations_made: bool = False
    current_recommendations: List[Dict] = field(default_factory=list)
    last_query: str = ""
    asked_questions: List[str] = field(default_factory=list)


class AssessmentAgent:
    """Main agent for handling assessment recommendations"""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.system_prompt = SYSTEM_PROMPT
        self._sessions: Dict[str, ConversationState] = {}
    
    def _get_session_state(self, session_id: Optional[str] = None) -> ConversationState:
        """Get or create session state"""
        if session_id is None:
            session_id = "default"
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState()
        return self._sessions[session_id]
    
    def process_message(
        self, 
        message: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return agent response.
        ALWAYS returns a dictionary with 'reply', 'recommendations', 'end_of_conversation'
        """
        
        # Default fallback response (in case anything fails)
        default_response = {
            "reply": "I need more information to help you find SHL assessments. What role or skills are you looking for?",
            "recommendations": [],
            "end_of_conversation": False
        }
        
        try:
            # Get session state
            state = self._get_session_state(session_id)
            
            # Update conversation history if provided
            if conversation_history is not None:
                state.messages = conversation_history.copy()
                # Reset turn count if history is reset
                if not conversation_history:
                    state.turn_count = 0
                    state.extracted_requirements = {}
                    state.recommendations_made = False
                    state.current_recommendations = []
                    state.asked_questions = []
            
            # Increment turn count
            state.turn_count += 1
            
            # Add user message to state
            state.messages.append({"role": "user", "content": message})
            
            # Check if conversation should end
            if state.turn_count >= settings.MAX_TURNS:
                return self._final_response(state)
            
            # Check if this is an off-topic query
            if self._is_off_topic(message):
                return {
                    "reply": "I specialize in SHL assessment recommendations. How can I help you find the right assessments for your hiring needs?",
                    "recommendations": [],
                    "end_of_conversation": False
                }
            
            # Extract requirements from full conversation history
            requirements = self._extract_requirements_from_history(state)
            state.extracted_requirements.update(requirements)
            
            # Check if this is a comparison request
            if self._is_comparison_request(message):
                comparison_result = self._handle_comparison(message, state)
                if comparison_result and isinstance(comparison_result, dict):
                    return comparison_result
                return default_response
            
            # Check if this is a refinement request
            refinement_response = self._handle_refinement(message, state)
            if refinement_response and isinstance(refinement_response, dict):
                return refinement_response
            
            # Decide action based on available information
            action = self._decide_action(state)
            
            if action == "ask":
                reply = self._generate_clarifying_question(state)
                return {
                    "reply": reply,
                    "recommendations": [],
                    "end_of_conversation": False
                }
            
            elif action == "search":
                results = self._search_assessments(state)
                state.current_recommendations = results
                
                if not results:
                    return {
                        "reply": "I couldn't find matching assessments. Could you provide more details about the role or skills?",
                        "recommendations": [],
                        "end_of_conversation": False
                    }
                
                state.recommendations_made = True
                return {
                    "reply": self._format_recommendations(results, state),
                    "recommendations": results[:10],
                    "end_of_conversation": state.turn_count >= settings.MAX_TURNS - 1
                }
            
            else:
                return {
                    "reply": "I'd be happy to help you find SHL assessments. What role or skills are you looking to assess?",
                    "recommendations": [],
                    "end_of_conversation": False
                }
                
        except Exception as e:
            print(f"[ERR] Error in process_message: {e}")
            return default_response
    
    def _extract_requirements_from_history(self, state: ConversationState) -> Dict[str, Any]:
        """Extract requirements from entire conversation history"""
        requirements = {}
        
        all_user_messages = " ".join([
            msg["content"] for msg in state.messages 
            if msg["role"] == "user"
        ])
        
        all_text = all_user_messages.lower()
        
        # Extract job role (expand keywords)
        roles = ["developer", "manager", "analyst", "engineer", "lead", "director", 
                 "architect", "consultant", "specialist", "administrator", "tester"]
        for role in roles:
            if role in all_text:
                requirements["job_role"] = role
                break
        
        # Extract skills (expand to include more)
        skills_list = ["java", "python", "javascript", "leadership", "communication", "personality", "cognitive", "ability", "reasoning", "verify", "numerical", "verbal", "manager", "opq", "aptitude", "inductive", "deductive", "managerial", "dependability", "safety", "multitasking", "general ability", "interactive", "thinking", "problem solving", "analytical", "technical", "business", "teamwork", "collaboration", "decision making", "planning", "organization", "attention to detail", "customer service", "sales", "marketing", "finance", "accounting", "engineering", "it", "software", "hardware", "database", "cloud", "security", "networking", "system administration", "project management", "agile", "scrum", "kanban", "waterfall", "devops", "ci/cd", "automation", "scripting", "testing", "quality assurance", "requirements analysis", "system design", "architecture", "integration", "deployment", "maintenance", "support", "training", "documentation", "sql", "aws", "docker", "react", "angular", "node", "spring", "backend", "frontend", "fullstack"]
        skills = [s for s in skills_list if s in all_text]
        if skills:
            requirements["skills"] = skills
        
        # Extract job level
        levels = ["entry", "junior", "mid", "senior", "lead", "manager", "director", "executive"]
        for level in levels:
            if level in all_text:
                requirements["job_level"] = level
                break
        
        # Extract test type from query
        test_type_keywords = {
            "personality": "P",
            "leadership": "P",
            "opq": "P",
            "cognitive": "A",
            "ability": "A", 
            "aptitude": "A",
            "reasoning": "A",
            "numerical": "A",
            "verbal": "A",
            "inductive": "A",
            "deductive": "A",
            "verify": "A",
            "knowledge": "K",
            "skill": "S",
            "technical": "S",
            "programming": "S"
        }
        for keyword, test_type in test_type_keywords.items():
            if keyword in all_text:
                requirements["test_type"] = test_type
                break
        
        return requirements
    def _is_off_topic(self, message: str) -> bool:
        """Check if message is off-topic"""
        off_topic_keywords = ["weather", "sports", "movie", "song", "recipe", "game", 
                              "politics", "stock", "price", "crypto", "bitcoin"]
        message_lower = message.lower()
        
        on_topic_keywords = ["assess", "test", "hire", "recruit", "candidate", "job", 
                            "role", "skill", "developer", "manager", "personality", 
                            "cognitive", "ability", "knowledge", "competency"]
        
        if any(keyword in message_lower for keyword in on_topic_keywords):
            return False
        
        return any(keyword in message_lower for keyword in off_topic_keywords)
    
    def _is_comparison_request(self, message: str) -> bool:
        """Check if user is asking for comparison"""
        message_lower = message.lower()
        compare_keywords = ["compare", "difference between", "vs", "versus", "differentiate"]
        return any(keyword in message_lower for keyword in compare_keywords)
    
    def _is_refinement_request(self, message: str) -> bool:
        """Check if user wants to refine recommendations"""
        # Only treat as refinement if the message explicitly asks to add/change something
        # AND we already have recommendations
        message_lower = message.lower()
        refine_phrases = ["add", "also include", "actually add", "instead show", "plus", "including"]
        test_types = ["personality", "cognitive", "ability", "knowledge", "skill"]
        
        # Must have explicit refinement phrase AND mention a test type
        has_refine = any(phrase in message_lower for phrase in refine_phrases)
        has_type = any(t in message_lower for t in test_types)
        
        # Also require that we have current recommendations to refine
        return has_refine and has_type
    
    def _get_catalog(self) -> List[Dict]:
        """Load catalog from processed file"""
        catalog_path = Path(settings.PROCESSED_CATALOG_PATH)
        if catalog_path.exists():
            with open(catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _find_assessment_fuzzy(self, name: str, catalog: List[Dict]) -> Optional[Dict]:
        """Fuzzy search for assessment by name"""
        name_lower = name.lower()
        
        for a in catalog:
            if a.get('name', '').lower() == name_lower:
                return a
        
        for a in catalog:
            if name_lower in a.get('name', '').lower():
                return a
        
        return None
    
    def _build_comparison_text(self, ass1: Dict, ass2: Dict) -> str:
        """Build comparison text between two assessments"""
        return f"""**Comparison: {ass1.get('name', 'N/A')} vs {ass2.get('name', 'N/A')}**

| Feature | {ass1.get('name', 'N/A')} | {ass2.get('name', 'N/A')} |
|---------|---------------------------|---------------------------|
| Test Type | {', '.join(ass1.get('test_types', [])) or 'General'} | {', '.join(ass2.get('test_types', [])) or 'General'} |
| Duration | {ass1.get('duration', 'N/A')} | {ass2.get('duration', 'N/A')} |
| Languages | {', '.join(ass1.get('languages', [])) or 'English'} | {', '.join(ass2.get('languages', [])) or 'English'} |
| Job Levels | {', '.join(ass1.get('job_levels', [])) or 'All'} | {', '.join(ass2.get('job_levels', [])) or 'All'} |

**Recommendation:** Choose based on your specific test type needs."""
    
    def _handle_comparison(self, message: str, state: ConversationState) -> Dict[str, Any]:
        """Handle assessment comparison requests"""
        names = re.findall(r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?)', message)
        common_words = {"compare", "between", "and", "vs", "versus", "difference"}
        names = [n for n in names if n.lower() not in common_words and len(n) > 2]
        
        if len(names) < 2:
            return {
                "reply": "Please specify two assessment names to compare (e.g., 'Compare Core Java and Java 8')",
                "recommendations": [],
                "end_of_conversation": False
            }
        
        catalog = self._get_catalog()
        if not catalog:
            return {
                "reply": "Catalog not loaded. Please ensure catalog data is available.",
                "recommendations": [],
                "end_of_conversation": False
            }
        
        ass1 = self._find_assessment_fuzzy(names[0], catalog)
        ass2 = self._find_assessment_fuzzy(names[1], catalog)
        
        if not ass1 or not ass2:
            return {
                "reply": f"Could not find both assessments. Please try exact assessment names.",
                "recommendations": [],
                "end_of_conversation": False
            }
        
        return {
            "reply": self._build_comparison_text(ass1, ass2),
            "recommendations": [ass1, ass2],
            "end_of_conversation": False
        }
    
    def _handle_refinement(self, message: str, state: ConversationState) -> Optional[Dict[str, Any]]:
        """Refine existing recommendations"""
        # Only refine if we have recommendations AND user explicitly asks to refine
        if not state.current_recommendations:
            return None
        # Check if message actually contains refinement keywords
        message_lower = message.lower()
        refine_phrases = ["add", "also include", "actually add", "instead show", "plus", "including"]
        if not any(phrase in message_lower for phrase in refine_phrases):
            return None
        
        message_lower = message.lower()
        filtered_results = state.current_recommendations.copy()
        
        if "personality" in message_lower:
            filtered_results = [r for r in filtered_results if "P" in r.get('test_types', [])]
        elif "cognitive" in message_lower or "ability" in message_lower:
            filtered_results = [r for r in filtered_results if "A" in r.get('test_types', [])]
        elif "knowledge" in message_lower:
            filtered_results = [r for r in filtered_results if "K" in r.get('test_types', [])]
        
        if not filtered_results:
            return {
                "reply": "No assessments match your refined criteria. Would you like to see the original recommendations?",
                "recommendations": state.current_recommendations[:5],
                "end_of_conversation": False
            }
        
        state.current_recommendations = filtered_results
        return {
            "reply": f"Based on your refinement, here are updated recommendations:\n\n{self._format_recommendations(filtered_results, state)}",
            "recommendations": filtered_results[:10],
            "end_of_conversation": False
        }
    
    def _search_assessments(self, state: ConversationState) -> List[Dict]:
        """Search for assessments based on extracted requirements"""
        query_parts = []
        
        if state.extracted_requirements.get("job_role"):
            query_parts.append(state.extracted_requirements["job_role"])
        if state.extracted_requirements.get("skills"):
            query_parts.extend(state.extracted_requirements["skills"])
        
        query = " ".join(query_parts) if query_parts else "assessment"
        state.last_query = query
        
        try:
            results = search_assessments(query, k=settings.TOP_K_RESULTS, return_type="metadata")
            return results if results else []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _decide_action(self, state: ConversationState) -> str:
        """Decide whether to ask or search"""
        if state.recommendations_made:
            return "ask"
        
        requirements = state.extracted_requirements
        has_role = bool(requirements.get("job_role"))
        has_skills = bool(requirements.get("skills"))
        has_test_type = bool(requirements.get("test_type"))
        
        # Search immediately if we have any actionable info
        if has_role or has_skills or has_test_type:
            return "search"
        
        # After turn 2, search anyway
        if state.turn_count >= 2:
            return "search"
        
        return "ask"

    def _generate_clarifying_question(self, state: ConversationState) -> str:
        """Generate a clarifying question"""
        requirements = state.extracted_requirements
        
        if not requirements.get("job_role") and not requirements.get("skills"):
            return "What role or skills are you looking to assess? For example: Java Developer, Project Manager, or specific skills like leadership or communication."
        
        if not requirements.get("job_role"):
            return "What job role are you hiring for (e.g., Software Engineer, Team Lead, Data Analyst)?"
        
        if not requirements.get("skills"):
            return f"For a {requirements.get('job_role')}, what specific skills are most important?"
        
        return "Based on your requirements, let me search for matching assessments."
    
    def _format_recommendations(self, results: List[Dict], state: ConversationState) -> str:
        """Format recommendations for chat reply"""
        if not results:
            return "I couldn't find matching assessments. Could you provide more details?"
        
        job_context = state.extracted_requirements.get('job_role', 'the role')
        reply = f"Based on your requirements for {job_context}, here are my top recommendations:\n\n"
        
        for i, assessment in enumerate(results[:5], 1):
            name = assessment.get('name', 'Unknown')
            test_types = assessment.get('test_types', ['General'])
            if isinstance(test_types, str):
                test_types = [test_types]
            duration = assessment.get('duration', 'Varies')
            reply += f"{i}. **{name}** ({', '.join(test_types)}) - {duration}\n"
        
        if len(results) > 5:
            reply += f"\nAnd {len(results) - 5} more assessments.\n"
        
        reply += "\nWould you like more details on any of these assessments?"
        return reply
    
    def _final_response(self, state: ConversationState) -> Dict[str, Any]:
        """Generate final response when conversation ends"""
        if state.recommendations_made:
            return {
                "reply": "We've reached the conversation limit. You can start a new session anytime for more recommendations.",
                "recommendations": state.current_recommendations[:10],
                "end_of_conversation": True
            }
        else:
            return {
                "reply": "I need more information to provide good recommendations. Please start a new conversation with more details.",
                "recommendations": [],
                "end_of_conversation": True
            }


# Singleton
_agent = None

def get_agent() -> AssessmentAgent:
    global _agent
    if _agent is None:
        _agent = AssessmentAgent()
    return _agent