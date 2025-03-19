from datetime import datetime

from pydantic import BaseModel


class AppointmentBase(BaseModel):
    user_id: int
    doctor_id: int
    appointment_time: datetime


class AppointmentCreate(AppointmentBase):
    pass


class Appointment(AppointmentBase):
    id: int
    status: str

    class Config:
        from_attributes = True
