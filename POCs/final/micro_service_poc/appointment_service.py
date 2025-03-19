import httpx  # For making requests to other services
from fastapi import FastAPI, HTTPException, Depends

app = FastAPI()

# Mock database (replace with PostgreSQL)
appointments_db = {}
# Mock URLs (replace with service discovery in a real system)
USER_SERVICE_URL = "http://localhost:8001"


async def get_user_from_user_service(user_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"User service unavailable: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"User not found by user service: {e.response.text}",
            )


@app.post("/appointments/")
async def create_appointment(
    appointment: dict, user: dict = Depends(get_user_from_user_service)
):
    # Basic validation (you'd add more)
    appointment_id = f"apt-{len(appointments_db) + 1}"
    appointment["appointment_id"] = appointment_id
    appointments_db[appointment_id] = appointment
    return appointment


@app.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: str):
    appointment = appointments_db.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
