from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.schemas.appointment import AppointmentRequest, AppointmentResponse
from app.db.database import get_db_session
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.services.auth import AuthService, oauth2_scheme

router = APIRouter()


@router.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_appointment(
    payload: AppointmentRequest,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    # Retrieve the current user (patient)
    current_user = await auth_service.get_current_user(token)

    # Verify that the provided doctor exists and is a doctor.
    query = select(User).where(User.id == payload.doctor_id, User.role == "doctor")
    result = await db.execute(query)
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found."
        )

    # Create the new appointment record using start_time and end_time
    new_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=payload.doctor_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=AppointmentStatus.scheduled,
        telemedicine_url=payload.telemedicine_url,
    )
    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)

    return new_appointment
