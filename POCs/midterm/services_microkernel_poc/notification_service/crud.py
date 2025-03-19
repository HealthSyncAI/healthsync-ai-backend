from datetime import datetime

from sqlalchemy.orm import Session

from . import models, schemas


def create_notification(db: Session, notification: schemas.NotificationCreate):
    db_notification = models.Notification(
        **notification.model_dump(), sent_at=datetime.now(), status="sent"
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification
