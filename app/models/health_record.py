from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    # Every health record is associated with a patient.
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Optionally record which doctor authored or modified the record.
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    record_data = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<HealthRecord id={self.id} for patient_id={self.patient_id}>"
