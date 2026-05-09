# app/services/agent.py

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
    """Track conversation state - DEFINED ONCE"""
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
        # Store states per session
        self._sessions: Dict[str, ConversationState] = {}
    
    def _get_session_state(self, session_id: str = None) -> ConversationState:
        """Get or create session state"""
        if session_id is None:
            session_id = "default"
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState()
        return self._sessions[session_id]
    
    def _extract_requirements_from_history(self, state: ConversationState) -> Dict[str, Any]:
        """Extract requirements from entire conversation history"""
        requirements = {}
        
        # Combine all user messages
        all_user_messages = " ".join([
            msg["content"] for msg in state.messages 
            if msg["role"] == "user"
        ])
        
        all_text = all_user_messages.lower()
        
        # Extract job role
        roles = ["developer", "manager", "analyst", "engineer", "lead", "director", 
                 "architect", "consultant", "specialist", "administrator"]
        for role in roles:
            if role in all_text:
                requirements["job_role"] = role
                break
        
        # Extract skills
        skills_list = ["java", "python", "javascript", "leadership", "communication", 
                       "sql", "aws", "docker", "agile", "project management", "react",
                       "angular", "node", "spring", "backend", "frontend", "fullstack"]
        skills = [s for s in skills_list if s in all_text]
        if skills:
            requirements["skills"] = skills
        
        # Extract job level
        levels = ["entry", "junior", "mid", "senior", "lead", "manager", "director", "executive"]
        for level in levels:
            if level in all_text:
                requirements["job_level"] = level
                break
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(min|minute|minutes|hour|hours)', all_text)
        if duration_match:
            num = int(duration_match.group(1))
            unit = duration_match.group(2)
            if 'hour' in unit:
                num = num * 60
            requirements["duration_limit"] = num
        
        # Extract test type preferences
        test_keywords = {
            "personality": "P",
            "cognitive": "A",
            "ability": "A",
            "knowledge": "K",
            "skill": "S",
            "competency": "C"
        }
        for keyword, test_type in test_keywords.items():
            if keyword in all_text:
                requirements["preferred_test_type"] = test_type
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
        
        # If it contains on-topic keywords, it's probably fine
        if any(keyword in message_lower for keyword in on_topic_keywords):
            return False
        
        return any(keyword in message_lower for keyword in off_topic_keywords)
    
    def _is_comparison_request(self, message: str) -> bool:
        """Check if user is asking for comparison"""
        message_lower = message.lower()
        compare_keywords = ["compare", "difference between", "vs", "versus", "differentiate", 
                           "contrast", "which is better", "tell me about"]
        return any(keyword in message_lower for keyword in compare_keywords)
    
    def _is_refinement_request(self, message: str) -> bool:
        """Check if user wants to refine recommendations"""
        message_lower = message.lower()
        refine_keywords = ["add", "also", "actually", "instead", "plus", "including", 
                          "excluding", "without", "only", "filter"]
        test_keywords = ["personality", "cognitive", "ability", "knowledge", "skill", 
                        "competency", "technical", "behavioral"]
        return any(kw in message_lower for kw in refine_keywords) and any(tk in message_lower for tk in test_keywords)
    
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
        
        # Exact match
        for a in catalog:
            if a.get('name', '').lower() == name_lower:
                return a
        
        # Partial match (name contains search term)
        for a in catalog:
            if name_lower in a.get('name', '').lower():
                return a
        
        # Keywords match
        keywords = name_lower.split()
        for a in catalog:
            a_name = a.get('name', '').lower()
            if any(kw in a_name for kw in keywords if len(kw) > 2):
                return a
        
        return None
    
    def _build_comparison_text(self, ass1: Dict, ass2: Dict) -> str:
        """Build comparison text between two assessments"""
        return f"""
**Comparison: {ass1.get('name', 'N/A')} vs {ass2.get('name', 'N/A')}**

| Feature | {ass1.get('name', 'N/A')} | {ass2.get('name', 'N/A')} |
|---------|---------------------------|---------------------------|
| Test Type | {', '.join(ass1.get('test_types', [])) or 'General'} | {', '.join(ass2.get('test_types', [])) or 'General'} |
| Duration | {ass1.get('duration', 'N/A')} | {ass2.get('duration', 'N/A')} |
| Languages | {', '.join(ass1.get('languages', [])) or 'English'} | {', '.join(ass2.get('languages', [])) or 'English'} |
| Job Levels | {', '.join(ass1.get('job_levels', [])) or 'All'} | {', '.join(ass2.get('job_levels', [])) or 'All'} |
| Remote Support | {ass1.get('remote_support', 'N/A')} | {ass2.get('remote_support', 'N/A')} |
| Adaptive | {ass1.get('adaptive', 'N/A')} | {ass2.get('adaptive', 'N/A')} |

**Description:**
- **{ass1.get('name', 'N/A')}**: {ass1.get('description', 'N/A')[:200]}...
- **{ass2.get('name', 'N/A')}**: {ass2.get('description', 'N/A')[:200]}...

**Recommendation:** 
- Choose **{ass1.get('name', 'N/A')}** if you need {', '.join(ass1.get('test_types', [])) or 'general'} assessment
- Choose **{ass2.get('name', 'N/A')}** if you need {', '.join(ass2.get('test_types', [])) or 'general'} assessment
"""
    
    def _handle_comparison(self, message: str, state: ConversationState) -> Dict[str, Any]:
        """Handle assessment comparison requests with fuzzy matching"""
        # Extract potential assessment names
        # Look for patterns like "Core Java" or "Java 8" or "OPQ and GSA"
        names = re.findall(r'([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?)', message)
        
        # Filter out common words
        common_words = {"compare", "between", "and", "vs", "versus", "difference", "what", "is", "the"}
        names = [n for n in names if n.lower() not in common_words and len(n) > 2]
        
        if len(names) < 2:
            return {
                "reply": "Please specify two assessment names to compare (e.g., 'Compare Core Java and Java 8' or 'What is the difference between OPQ and GSA?')",
                "recommendations": [],
                "end_of_conversation": False
            }
        
        # Get catalog
        catalog = self._get_catalog()
        
        if not catalog:
            return {
                "reply": "Catalog not loaded. Please ensure catalog data is available.",
                "recommendations": [],
                "end_of_conversation": False
            }
        
        # Find both assessments
        ass1 = self._find_assessment_fuzzy(names[0], catalog)
        ass2 = self._find_assessment_fuzzy(names[1], catalog)
        
        if not ass1 or not ass2:
            found_names = []
            if ass1:
                found_names.append(ass1.get('name', names[0]))
            if ass2:
                found_names.append(ass2.get('name', names[1]))
            
            return {
                "reply": f"Could not find both assessments. Found: {', '.join(found_names) if found_names else 'neither'}. Please try exact assessment names from the catalog.",
                "recommendations": [],
                "end_of_conversation": False
            }
        
        comparison = self._build_comparison_text(ass1, ass2)
        return {
            "reply": comparison,
            "recommendations": [ass1, ass2],
            "end_of_conversation": False
        }
    
    def _handle_refinement(self, message: str, state: ConversationState) -> Dict[str, Any]:
        """Refine existing recommendations"""
        if not state.current_recommendations:
            return None
        
        message_lower = message.lower()
        filtered_results = state.current_recommendations.copy()
        
        # Apply filters based on message
        if "personality" in message_lower:
            filtered_results = [r for r in filtered_results if "P" in r.get('test_types', [])]
        elif "cognitive" in message_lower or "ability" in message_lower:
            filtered_results = [r for r in filtered_results if "A" in r.get('test_types', [])]
        elif "knowledge" in message_lower:
            filtered_results = [r for r in filtered_results if "K" in r.get('test_types', [])]
        elif "skill" in message_lower:
            filtered_results = [r for r in filtered_results if "S" in r.get('test_types', [])]
        elif "competency" in message_lower:
            filtered_results = [r for r in filtered_results if "C" in r.get('test_types', [])]
        
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
        
        # Build search query from all extracted requirements
        query_parts = []
        
        if state.extracted_requirements.get("job_role"):
            query_parts.append(state.extracted_requirements["job_role"])
        
        if state.extracted_requirements.get("skills"):
            query_parts.extend(state.extracted_requirements["skills"])
        
        if state.extracted_requirements.get("job_level"):
            query_parts.append(state.extracted_requirements["job_level"])
        
        query = " ".join(query_parts) if query_parts else "assessment"
        state.last_query = query
        
        try:
            results = search_assessments(query, k=settings.TOP_K_RESULTS, return_type="metadata")
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _decide_action(self, state: ConversationState) -> str:
        """Decide whether to ask or search based on accumulated info"""
        
        if state.recommendations_made:
            return "ask"
        
        requirements = state.extracted_requirements
        has_role = bool(requirements.get("job_role"))
        has_skills = bool(requirements.get("skills"))
        has_duration = bool(requirements.get("duration_limit"))
        
        # If we have role OR skills, that's enough to search
        if (has_role or has_skills) and state.turn_count >= 2:
            return "search"
        
        # If we have duration but no role/skills, ask for role
        if has_duration and not (has_role or has_skills):
            return "ask"
        
        # If this is turn 3+, search even with minimal info
        if state.turn_count >= 3:
            return "search"
        
        return "ask"
    
    def _generate_clarifying_question(self, state: ConversationState) -> str:
        """Generate a clarifying question based on what's missing"""
        
        requirements = state.extracted_requirements
        
        # Track what we've already asked
        asked = state.asked_questions
        
        if not requirements.get("job_role") and not requirements.get("skills"):
            if "role" not in asked:
                state.asked_questions.append("role")
                return "What role or skills are you looking to assess? For example: Java Developer, Project Manager, or specific skills like leadership or communication."
        
        if not requirements.get("job_role") and requirements.get("skills"):
            if "role_specific" not in asked:
                state.asked_questions.append("role_specific")
                return f"I see you're interested in {', '.join(requirements.get('skills', []))}. What job role are you hiring for (e.g., Software Engineer, Team Lead, Data Analyst)?"
        
        if not requirements.get("skills") and requirements.get("job_role"):
            if "skills" not in asked:
                state.asked_questions.append("skills")
                return f"For a {requirements.get('job_role')}, what specific skills are most important to assess?"
        
        if not requirements.get("duration_limit"):
            if "duration" not in asked:
                state.asked_questions.append("duration")
                return "How long should the assessment be? (e.g., 30 minutes, 60 minutes)"
        
        if not requirements.get("job_level"):
            if "level" not in asked:
                state.asked_questions.append("level")
                return "What job level are you hiring for? (Entry, Mid, Senior, Manager, Executive)"
        
        return "Could you provide more details about your assessment needs? For example, specific test types (Knowledge, Personality, Ability, Skills) or languages?"
    
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
                "reply": "I need more information to provide good recommendations. Please start a new conversation with more details about your requirements.",
                "recommendations": [],
                "end_of_conversation": True
            }
    
    def process_message(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process a user message and return agent response"""
        
        # Get session state
        state = self._get_session_state(session_id)
        
        # Update conversation history if provided
        if conversation_history:
            state.messages = conversation_history.copy()
        
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
            return self._handle_comparison(message, state)
        
        # Check if this is a refinement request
        refinement_response = self._handle_refinement(message, state)
        if refinement_response:
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
                reply = "I couldn't find matching assessments. Could you provide more details about the role or skills?"
                return {
                    "reply": reply,
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


# Singleton
_agent = None

def get_agent() -> AssessmentAgent:
    global _agent
    if _agent is None:
        _agent = AssessmentAgent()
    return _agent