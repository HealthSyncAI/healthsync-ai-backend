from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from .database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id")
    )  # Assuming users from user_service
    message = Column(String)
    sent_at = Column(DateTime)
    status = Column(String)  # e.g., "pending", "sent", "failed"
