import enum

from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum
from sqlalchemy.sql import func

from app.db.database import Base

class AppointmentStatus(enum.Enum):
    scheduled = "scheduled"
    cancelled = "cancelled"
    completed = "completed"

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(
        Enum(AppointmentStatus), default=AppointmentStatus.scheduled, nullable=False
    )
    telemedicine_url = Column(String(200), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (f"<Appointment id={self.id} status={self.status.value} "
                f"start={self.start_time} end={self.end_time}>")