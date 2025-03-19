from fastapi import FastAPI, HTTPException, Body
import httpx
from pydantic import BaseModel

app = FastAPI()

# Base URLs for the services (in a real setup, these would be configurable)
AUTH_SERVICE_URL = "http://localhost:8001"
APPOINTMENT_SERVICE_URL = "http://localhost:8002"
SYMPTOM_SERVICE_URL = "http://localhost:8003"
NOTIFICATION_SERVICE = "http://localhost:8004"

class AppointmentRequest(BaseModel): #Using Pydantic for request validation
    patient_id: int
    symptom: str
    appointment_time: str

@app.post("/schedule_appointment")
async def schedule_appointment(appointment_request: AppointmentRequest):
    """
    Orchestrates the appointment scheduling process.
    """
    patient_id = appointment_request.patient_id
    symptom = appointment_request.symptom
    appointment_time = appointment_request.appointment_time

    try:
        # 1. Authenticate User
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(f"{AUTH_SERVICE_URL}/authenticate", json={"user_id": patient_id})
            auth_response.raise_for_status()  # Raise an exception for bad status codes
            token = auth_response.json().get("token")
            if not token:
                raise HTTPException(status_code=401, detail="Authentication failed")

        # 2. Check Symptoms (Simplified)
        async with httpx.AsyncClient() as client:
            symptom_response = await client.post(f"{SYMPTOM_SERVICE_URL}/check_symptom", json={"symptom": symptom}, headers={"Authorization": f"Bearer {token}"})
            symptom_response.raise_for_status()
            recommendation = symptom_response.json().get("recommendation")
            if recommendation != "See a doctor":
              return {"message": "Based on the symptom check. "+ recommendation}

        # 3. Schedule Appointment
        async with httpx.AsyncClient() as client:
            appointment_response = await client.post(f"{APPOINTMENT_SERVICE_URL}/schedule", json={"patient_id": patient_id, "time": appointment_time}, headers={"Authorization": f"Bearer {token}"})
            appointment_response.raise_for_status()
            appointment_id = appointment_response.json().get("appointment_id")

        # 4. Send notification
        async with httpx.AsyncClient() as client:
          notification_response = await client.post(f"{NOTIFICATION_SERVICE}/notify", json={"patient_id": patient_id, "message": f"Your appointment is scheduled. ID: {appointment_id}"}, headers={"Authorization": f"Bearer {token}"})
          notification_response.raise_for_status()

        return {"message": f"Appointment scheduled successfully.  Appointment ID: {appointment_id}", "recommendation": recommendation}

    except httpx.HTTPError as e:
        # Handle HTTP errors (e.g., service unavailable)
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    