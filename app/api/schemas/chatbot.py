from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class SymptomRequest(BaseModel):
    symptom_text: str

    room_number: Optional[int] = None


class ChatbotResponse(BaseModel):
    input_text: str
    analysis: str
    triage_advice: Optional[str] = None
    model_response: Optional[str] = None


class ChatSessionOut(BaseModel):
    id: int
    input_text: str
    analysis: Optional[str] = Field(None, alias="model_response")
    triage_advice: Optional[str] = None
    created_at: datetime
    room_number: int
    model_config = ConfigDict(from_attributes=True)


class ChatRoomChats(BaseModel):
    room_number: int
    chats: List[ChatSessionOut]
