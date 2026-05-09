# app/api/routes.py

from fastapi import APIRouter, HTTPException
from typing import List

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    Recommendation,
    Message
)
from app.services.agent import get_agent
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint for assessment recommendations
    """
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    latest_message = request.messages[-1].content
    
    conversation_history = [
        {"role": msg.role, "content": msg.content} 
        for msg in request.messages[:-1]
    ]
    
    agent = get_agent()
    response = agent.process_message(latest_message, conversation_history)
    
    recommendations = []
    for rec in response.get("recommendations", [])[:10]:
        if isinstance(rec, dict):
            test_types = rec.get("test_types", [])
            if isinstance(test_types, str):
                test_types = [test_types]
            primary_test_type = test_types[0] if test_types else "General"
            
            recommendations.append(
                Recommendation(
                    name=rec.get("name", "Unknown"),
                    url=rec.get("url", "#"),
                    test_type=primary_test_type
                )
            )
    
    return ChatResponse(
        reply=response.get("reply", "I couldn't process your request."),
        recommendations=recommendations,
        end_of_conversation=response.get("end_of_conversation", False)
    )