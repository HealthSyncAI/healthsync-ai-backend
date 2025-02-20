from datetime import datetime

from pydantic import BaseModel


class ChatSessionBase(BaseModel):
    user_id: int
    start_time: datetime


class ChatSessionCreate(ChatSessionBase):
    messages: str


class ChatSession(ChatSessionBase):
    id: int
    end_time: datetime | None = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    user_input: str


class ChatResponse(BaseModel):
    response: str
    # triage_level: Optional[str] = None  #  e.g., "low", "medium", "high"
