from sqlalchemy.orm import Session

from . import models, schemas


def create_health_record(
    db: Session, health_record: schemas.HealthRecordCreate, file_content: bytes
):
    db_health_record = models.HealthRecord(
        **health_record.model_dump(), data=file_content
    )
    db.add(db_health_record)
    db.commit()
    db.refresh(db_health_record)
    return db_health_record
