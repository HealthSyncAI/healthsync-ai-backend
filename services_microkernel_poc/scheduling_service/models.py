from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Link to User Service
    doctor_id = Column(Integer)  # Ideally, also a ForeignKey, but simplified
    appointment_time = Column(DateTime)
    status = Column(String, default="scheduled")

    user = relationship("User")  # Requires User model, even if in another service
