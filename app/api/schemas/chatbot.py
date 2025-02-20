from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class SymptomRequest(BaseModel):
    symptom_text: str


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
    model_config = ConfigDict(from_attributes=True)
