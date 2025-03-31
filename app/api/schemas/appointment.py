from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AppointmentRequest(BaseModel):
    doctor_id: int

    start_time: datetime
    end_time: datetime
    telemedicine_url: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    start_time: datetime
    end_time: datetime
    status: str
    telemedicine_url: Optional[str] = None

    class Config:
        orm_mode = True
