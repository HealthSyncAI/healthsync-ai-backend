from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

#  We'd also import User from user_service.models if we were doing cross-service joins
# from user_service.models import User

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/appointments/", response_model=schemas.Appointment)
def create_appointment(
    appointment: schemas.AppointmentCreate, db: Session = Depends(get_db)
):
    # Basic conflict check (simplified for POC)
    existing_appointment = crud.get_appointment_by_time_and_doctor(
        db,
        appointment_time=appointment.appointment_time,
        doctor_id=appointment.doctor_id,
    )
    if existing_appointment:
        raise HTTPException(status_code=409, detail="Appointment slot already booked")
    return crud.create_appointment(db=db, appointment=appointment)


@app.get("/appointments/", response_model=List[schemas.Appointment])
def read_appointments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    appointments = crud.get_appointments(db, skip=skip, limit=limit)
    return appointments


@app.get("/appointments/{appointment_id}", response_model=schemas.Appointment)
def read_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = crud.get_appointment(db, appointment_id=appointment_id)
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment
