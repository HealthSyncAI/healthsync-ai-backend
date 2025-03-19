from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/notifications/", response_model=schemas.Notification)
def create_notification(
    notification: schemas.NotificationCreate, db: Session = Depends(get_db)
):
    # In a real system, you'd likely have a queue and a worker process.
    # For the POC, we'll just create the notification and mark it as sent.
    return crud.create_notification(db=db, notification=notification)
