from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_
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
import logging

logger = logging.getLogger(__name__)
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
    try:
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
        await db.flush()
        await db.refresh(new_appointment)

        triage_record = await create_triage_record_from_chats(
            db, current_user.id, payload.doctor_id
        )
        if triage_record is None:

            logger.warning(
                f"Could not create triage record for patient {current_user.id} during appointment scheduling."
            )

        await db.commit()
        await db.refresh(new_appointment)

        return new_appointment

    except HTTPException as http_exc:

        raise http_exc
    except Exception as exc:
        logger.error(
            f"Error scheduling appointment for user {current_user.id if 'current_user' in locals() else 'unknown'}: {exc}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while scheduling the appointment.",
        )


@router.get(
    "/my-appointments",
    response_model=List[AppointmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all appointments for the current user (patient or doctor)",
    description="Retrieves a list of all appointments associated with the currently authenticated user, "
    "regardless of whether they are the patient or the doctor in the appointment.",
)
async def get_my_appointments(
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves all appointments linked to the current authenticated user's ID,
    covering both cases where the user is the patient and where the user is the doctor.
    """
    try:
        current_user: User = await auth_service.get_current_user(token)

        query = (
            select(Appointment)
            .where(
                or_(
                    Appointment.patient_id == current_user.id,
                    Appointment.doctor_id == current_user.id,
                )
            )
            .order_by(Appointment.start_time.desc())
        )

        result = await db.execute(query)
        appointments = result.scalars().all()
        return appointments
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(
            f"Error fetching appointments for user {current_user.id if 'current_user' in locals() else 'unknown'}: {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointments.",
        )


@router.get("/{appointment_id}/health-records", response_model=List[HealthRecordOut])
async def get_patient_health_records_for_doctor(
    appointment_id: int,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Get health records for a patient that a doctor is seeing."""
    try:
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
                detail="Appointment not found or you don't have permission to access associated records.",
            )

        if (
            current_user.id != appointment.doctor_id
            and current_user.id != appointment.patient_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access health records for this appointment.",
            )

        records = await get_patient_health_records(db, appointment.patient_id)
        return records
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(
            f"Error fetching health records for appointment {appointment_id} by user {current_user.id if 'current_user' in locals() else 'unknown'}: {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient health records for the appointment.",
        )


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
    try:
        await auth_service.get_current_user(token)
        doctors = await get_available_doctors(db, specialization)
        return doctors
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(
            f"Error listing available doctors (specialization: {specialization}): {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve list of doctors.",
        )


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
    try:
        await auth_service.get_current_user(token)
        doctor = await get_doctor_by_id(db, doctor_id)

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found"
            )

        return doctor
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(f"Error retrieving details for doctor ID {doctor_id}: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve doctor details.",
        )
