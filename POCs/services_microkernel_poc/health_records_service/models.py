from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary

from .database import Base


class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Link to User Service
    record_type = Column(String)  # e.g., "lab_result", "prescription"
    data = Column(
        LargeBinary
    )  # Store as bytes (e.g., a PDF, image) - NOT RECOMMENDED FOR REAL DATA
