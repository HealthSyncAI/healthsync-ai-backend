from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    # Only patients use the pre-screening chatbot.
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    input_text = Column(Text, nullable=False)
    voice_transcription = Column(Text, nullable=True)  # Optional, if voice input is available.
    deepseek_response = Column(Text, nullable=True)
    triage_advice = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ChatSession id={self.id} for patient_id={self.patient_id}>"
