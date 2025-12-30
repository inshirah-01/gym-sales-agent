from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent_level: Optional[str] = None
    booking_made: bool = False

class IntentClassification(BaseModel):
    intent_level: Literal["high", "medium", "low"]
    reasoning: str
    key_indicators: list[str]

class BookingRequest(BaseModel):
    user_email: str
    user_name: str
    preferred_time: str
    
class BookingResponse(BaseModel):
    success: bool
    booking_url: Optional[str] = None
    scheduled_time: Optional[str] = None
    message: str


class LeadMemory(BaseModel):
    """Structured lead memory"""
    fitness_goals: str = "Unknown"
    past_experience: str = "Unknown"
    location_proximity: str = "Unknown"
    joining_timeline: str = "Unknown"
    motivation: str = "Unknown"
    preferred_time: str = "Unknown"
    health_physical_info: str = "Unknown"
    objections: str = "None"
    conversation_summary: str = "None"
    total_messages: int = 0
    last_intent: str = "unknown"

class MemoryUpdateRequest(BaseModel):
    """Memory update request from main agent"""
    session_id: str
    user_message: str
    agent_response: str