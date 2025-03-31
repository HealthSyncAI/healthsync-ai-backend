from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.schemas.appointment import AppointmentRequest, AppointmentResponse
from app.api.schemas.doctor import DoctorList, DoctorDetail
from app.api.schemas.health_record import HealthRecordOut
from app.db.database import get_db_session
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.services.auth import AuthService, oauth2_scheme
from app.services.doctor import get_available_doctors, get_doctor_by_id
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
    current_user = await auth_service.get_current_user(token)
    query = select(User).where(User.id == payload.doctor_id, User.role == "doctor")
    result = await db.execute(query)
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found."
        )

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
    await auth_service.get_current_user(token)
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
    await auth_service.get_current_user(token)
    doctor = await get_doctor_by_id(db, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found"
        )

    return doctor
