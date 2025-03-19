from sqlalchemy.orm import Session

from . import models, schemas
from datetime import datetime


def get_appointment(db: Session, appointment_id: int):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id)
        .first()
    )


def get_appointments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Appointment).offset(skip).limit(limit).all()


def create_appointment(db: Session, appointment: schemas.AppointmentCreate):
    db_appointment = models.Appointment(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def get_appointment_by_time_and_doctor(
    db: Session, appointment_time: datetime, doctor_id: int
):
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.appointment_time == appointment_time,
            models.Appointment.doctor_id == doctor_id,
        )
        .first()
    )
