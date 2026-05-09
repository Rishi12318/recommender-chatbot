# app/api/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional


class Message(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "I need an assessment for Java developers"
            }
        }


class ChatRequest(BaseModel):
    """Request model for /chat endpoint"""
    messages: List[Message] = Field(..., description="Conversation history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "I need an assessment for Java developers"}
                ]
            }
        }


class Recommendation(BaseModel):
    """Assessment recommendation model"""
    name: str = Field(..., description="Assessment name")
    url: str = Field(..., description="Assessment URL")
    test_type: str = Field(..., description="Test type (K, P, A, S, C)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Java Programming Test",
                "url": "https://www.shl.com/assessments/java",
                "test_type": "K"
            }
        }


class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    reply: str = Field(..., description="Agent's reply message")
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="List of recommended assessments (1-10 items)"
    )
    end_of_conversation: bool = Field(
        default=False,
        description="Whether the conversation should end"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "Here are recommended assessments for Java developers.",
                "recommendations": [
                    {
                        "name": "Java Programming Test",
                        "url": "https://www.shl.com/assessments/java",
                        "test_type": "K"
                    }
                ],
                "end_of_conversation": False
            }
        }