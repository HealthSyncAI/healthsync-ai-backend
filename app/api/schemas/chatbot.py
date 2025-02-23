from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class SymptomRequest(BaseModel):
    symptom_text: str
    # Optional: allow the client to specify an existing room number.
    # If None, a new chat room will be created.
    room_number: Optional[int] = None


class ChatbotResponse(BaseModel):
    input_text: str
    analysis: str
    triage_advice: Optional[str] = None
    model_response: Optional[str] = None


class ChatSessionOut(BaseModel):
    id: int
    input_text: str
    # We alias analysis to the model_response field from the ORM.
    analysis: Optional[str] = Field(None, alias="model_response")
    triage_advice: Optional[str] = None
    created_at: datetime
    # Include the room number from the related chat room.
    room_number: int

    model_config = ConfigDict(from_attributes=True)


class ChatRoomChats(BaseModel):
    # This new schema is used to group chats by room number.
    room_number: int
    chats: List[ChatSessionOut]
