from datetime import datetime

from pydantic import BaseModel


class NotificationBase(BaseModel):
    user_id: int
    message: str


class NotificationCreate(NotificationBase):
    pass


class Notification(NotificationBase):
    id: int
    sent_at: datetime
    status: str

    class Config:
        from_attributes = True
