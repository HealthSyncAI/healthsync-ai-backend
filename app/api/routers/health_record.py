from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.health_record import (
    HealthRecordOut,
    DoctorRecordCreate,
    HealthRecordCreate,
)
from app.db.database import get_db_session
from app.services.auth import AuthService, oauth2_scheme
from app.services.health_record import (
    create_health_record,
    get_patient_health_records,
    get_health_record_by_id,
)
from app.models.user import UserRole
from app.models.health_record import RecordType

router = APIRouter()


@router.post("/", response_model=HealthRecordOut, status_code=status.HTTP_201_CREATED)
async def add_health_record(
    record: HealthRecordCreate,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new health record. Only doctors can create records directly."""
    current_user = await auth_service.get_current_user(token)

    if current_user.role != UserRole.doctor and current_user.id != record.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can create health records for patients",
        )

    return await create_health_record(db, record, current_user.id)


@router.post(
    "/doctor-note", response_model=HealthRecordOut, status_code=status.HTTP_201_CREATED
)
async def add_doctor_note(
    record: DoctorRecordCreate,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new doctor's note for a patient."""
    current_user = await auth_service.get_current_user(token)

    if current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can create medical notes",
        )

    health_record = HealthRecordCreate(
        title=record.title,
        summary=record.summary,
        record_type=RecordType.doctor_note,
        patient_id=record.patient_id,
        doctor_id=current_user.id,
        symptoms=record.symptoms,
        diagnosis=record.diagnosis,
        treatment_plan=record.treatment_plan,
        medication=record.medication,
    )

    return await create_health_record(db, health_record, current_user.id)


@router.get("/patient/{patient_id}", response_model=List[HealthRecordOut])
async def get_patient_records(
    patient_id: int,
    record_type: Optional[str] = Query(None),
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all health records for a specific patient."""
    current_user = await auth_service.get_current_user(token)

    if current_user.id != patient_id and current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access these records",
        )

    return await get_patient_health_records(db, patient_id, record_type)


@router.get("/{record_id}", response_model=HealthRecordOut)
async def get_record(
    record_id: int,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a specific health record by ID."""
    current_user = await auth_service.get_current_user(token)

    record = await get_health_record_by_id(db, record_id)

    if current_user.id != record.patient_id and current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this record",
        )

    return record
