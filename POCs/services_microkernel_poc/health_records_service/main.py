from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

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


@app.post("/health_records/", response_model=schemas.HealthRecord)
async def create_health_record(
    user_id: int, record_type: str, file: UploadFile, db: Session = Depends(get_db)
):
    # VERY simplified.  In a real system, you'd handle security,
    # storage location, and potentially encryption.
    contents = await file.read()
    health_record = schemas.HealthRecordCreate(user_id=user_id, record_type=record_type)
    return crud.create_health_record(
        db=db, health_record=health_record, file_content=contents
    )
