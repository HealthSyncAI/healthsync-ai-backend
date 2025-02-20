from sqlalchemy.orm import Session

from . import models, schemas
from datetime import datetime


def create_chat_session(db: Session, chat_session: schemas.ChatSessionCreate):
    db_chat_session = models.ChatSession(**chat_session.model_dump())
    db.add(db_chat_session)
    db.commit()
    db.refresh(db_chat_session)
    return db_chat_session


def update_chat_session(db: Session, chat_session_id: int, updated_messages: str):
    chat_session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == chat_session_id)
        .first()
    )
    chat_session.messages = f"{chat_session.messages}\nBot: {updated_messages}"
    chat_session.end_time = datetime.now()
    db.commit()
    db.refresh(chat_session)
    return chat_session
