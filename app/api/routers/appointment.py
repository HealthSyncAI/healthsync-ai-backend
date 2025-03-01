from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.api.schemas.appointment import AppointmentRequest, AppointmentResponse
from app.api.schemas.health_record import HealthRecordOut
from app.api.schemas.doctor import DoctorList, DoctorDetail
from app.services.doctor import get_available_doctors, get_doctor_by_id
from app.db.database import get_db_session
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.services.auth import AuthService, oauth2_scheme
from app.services.health_record import (
    create_triage_record_from_chats,
    get_patient_health_records,
)

router = APIRouter()


@router.post(
    "/",
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

    # Generate a health record from the patient's chat history
    await create_triage_record_from_chats(db, current_user.id, payload.doctor_id)

    return new_appointment


@router.get("/{appointment_id}/health-records", response_model=List[HealthRecordOut])
async def get_patient_health_records_for_doctor(
    appointment_id: int,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Get health records for a patient that a doctor is seeing."""
    current_user = await auth_service.get_current_user(token)

    # Verify this is a valid appointment and the doctor has rights to see it
    query = select(Appointment).where(
        Appointment.id == appointment_id,
        (Appointment.doctor_id == current_user.id)
        | (Appointment.patient_id == current_user.id),
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or you don't have permission to access it.",
        )

    # Get the patient's health records
    records = await get_patient_health_records(db, appointment.patient_id)
    return records


@router.get("/doctors", response_model=List[DoctorList], status_code=status.HTTP_200_OK)
async def list_available_doctors(
    specialization: Optional[str] = Query(
        None, description="Filter doctors by specialization"
    ),
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a list of available doctors with their basic information."""
    # Authenticate user (patient or doctor can view this)
    await auth_service.get_current_user(token)

    # Get available doctors, filtered by specialization if provided
    doctors = await get_available_doctors(db, specialization)

    return doctors


@router.get(
    "/doctors/{doctor_id}", response_model=DoctorDetail, status_code=status.HTTP_200_OK
)
async def get_doctor_details(
    doctor_id: int,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific doctor."""
    # Authenticate user (patient or doctor can view this)
    await auth_service.get_current_user(token)

    # Get the doctor details
    doctor = await get_doctor_by_id(db, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found"
        )

    return doctor
