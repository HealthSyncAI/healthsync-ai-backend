from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text,
    DateTime,
    String,
    JSON,
    Float,
    Enum,
)
import enum
from sqlalchemy.sql import func

from app.db.database import Base


class RecordType(enum.Enum):
    at_triage = "at_triage"
    doctor_note = "doctor_note"


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)

    # Record type to differentiate different kinds of records
    record_type = Column(Enum(RecordType), nullable=False)

    # Basic content
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)

    # Structured data
    symptoms = Column(JSON, nullable=True)  # Array of symptoms with severity
    diagnosis = Column(JSON, nullable=True)  # Can include ICD-10 codes
    treatment_plan = Column(JSON, nullable=True)
    medication = Column(JSON, nullable=True)

    # For chatbot-generated records
    triage_recommendation = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in triage

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<HealthRecord id={self.id} type={self.record_type.value} for patient_id={self.patient_id}>"
