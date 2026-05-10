# app/services/llm_client.py

import os
from typing import List, Dict, Any, Optional
from app.core.config import settings

class LLMClient:
    """Wrapper for LLM API calls"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        try:
            if self.provider == "groq":
                from groq import Groq
                if not settings.GROQ_API_KEY:
                    print("[!] GROQ_API_KEY not set. Running in mock mode.")
                    return
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                print(f"[OK] Initialized Groq client with model: {self.model}")
                
            elif self.provider == "gemini":
                import google.generativeai as genai
                if not settings.GEMINI_API_KEY:
                    print("[!] GEMINI_API_KEY not set. Running in mock mode.")
                    return
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.client = genai.GenerativeModel(self.model)
                print(f"[OK] Initialized Gemini client with model: {self.model}")
                
            elif self.provider == "openai":
                from openai import OpenAI
                if not settings.OPENAI_API_KEY:
                    print("[!] OPENAI_API_KEY not set. Running in mock mode.")
                    return
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                print(f"[OK] Initialized OpenAI client with model: {self.model}")
            else:
                print(f"[!] Unknown provider: {self.provider}, using mock client")
                self.client = None
                
        except ImportError as e:
            print(f"[!] Could not import {self.provider} library: {e}")
            print("   Install with: pip install groq (or google-generativeai, openai)")
            self.client = None
        except Exception as e:
            print(f"[!] Failed to initialize {self.provider}: {e}")
            self.client = None
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Send chat message to LLM and get response"""
        
        # Mock client for testing without API keys
        if self.client is None:
            return self._mock_response(messages)
        
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                )
                return response.choices[0].message.content
            
            elif self.provider == "gemini":
                # Convert OpenAI format to Gemini format
                prompt = "\n".join([m["content"] for m in messages if m["role"] != "system"])
                response = self.client.generate_content(prompt)
                return response.text
            
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                )
                return response.choices[0].message.content
            
        except Exception as e:
            print(f"[ERR] LLM API error: {e}")
            return self._mock_response(messages)
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Mock response for testing without API keys"""
        last_message = messages[-1]["content"].lower() if messages else ""
        
        if "java" in last_message or "developer" in last_message:
            return "I understand you're looking for assessments for a developer role. Could you specify the programming language or specific skills required?"
        elif "leadership" in last_message or "manager" in last_message:
            return "For leadership roles, I recommend our management and leadership assessments. What level of leadership are you hiring for (team lead, manager, director)?"
        elif "cognitive" in last_message or "aptitude" in last_message:
            return "Our cognitive ability tests range from 20-40 minutes. Do you have any time constraints or specific cognitive areas to focus on?"
        else:
            return "I'd be happy to help find the right SHL assessments. Could you tell me more about the role or skills you need to assess?"

# Singleton
_llm_client = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client