from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)

    input_text = Column(Text, nullable=False)
    voice_transcription = Column(
        Text, nullable=True
    )  # Optional, if voice input is available.
    model_response = Column(Text, nullable=True)
    triage_advice = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chat_room = relationship("ChatRoom", back_populates="sessions")

    def __repr__(self):
        return (
            f"<ChatSession id={self.id} for patient_id={self.patient_id} "
            f"in chat_room_id={self.chat_room_id}>"
        )

    @property
    def room_number(self):

        return self.chat_room.room_number if self.chat_room else None
