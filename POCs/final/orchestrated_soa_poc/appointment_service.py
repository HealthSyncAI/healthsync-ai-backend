from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()

# Mock appointment database (In a real application, use a real database)
appointments = {}
next_appointment_id = 1


class AppointmentRequest(BaseModel):
    patient_id: int
    time: str


def verify_token(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    if token != "mock_token_123":  # Validate the mock token
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/schedule")
async def schedule_appointment(
    appointment_request: AppointmentRequest, authorization: Optional[str] = Header(None)
):
    """
    Schedules an appointment.
    """
    verify_token(authorization)
    global next_appointment_id
    appointment_id = next_appointment_id
    appointments[appointment_id] = {
        "patient_id": appointment_request.patient_id,
        "time": appointment_request.time,
        "status": "scheduled",
    }
    next_appointment_id += 1
    return {"appointment_id": appointment_id}
