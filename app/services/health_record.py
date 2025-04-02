import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.health_record import (
    HealthRecordCreate,
    SymptomItem,
    DiagnosisItem,
    TreatmentPlanItem,
    MedicationItem,
)
from app.models.health_record import HealthRecord, RecordType
from app.models.chat_session import ChatSession
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def _serialize_list_items(
    items: Optional[List[BaseModel]],
) -> Optional[List[Dict[str, Any]]]:
    """Helper to serialize Pydantic models to dicts, handling None."""
    if items is None:
        return None

    return [item.model_dump(exclude_unset=True) for item in items]


async def create_health_record(
    db: AsyncSession, record_data: HealthRecordCreate, creator_id: int
) -> HealthRecord:
    """Create a new health record."""
    try:

        doc_id = (
            record_data.doctor_id if record_data.doctor_id is not None else creator_id
        )

        new_record = HealthRecord(
            patient_id=record_data.patient_id,
            doctor_id=doc_id,
            chat_session_id=record_data.chat_session_id,
            record_type=record_data.record_type,
            title=record_data.title,
            summary=record_data.summary,
            symptoms=_serialize_list_items(record_data.symptoms),
            diagnosis=_serialize_list_items(record_data.diagnosis),
            treatment_plan=_serialize_list_items(record_data.treatment_plan),
            medication=_serialize_list_items(record_data.medication),
            triage_recommendation=record_data.triage_recommendation,
            confidence_score=record_data.confidence_score,
        )

        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)

        logger.info(
            f"Created health record id={new_record.id} (type: {new_record.record_type.value}) for patient {record_data.patient_id}"
        )
        return new_record

    except Exception as exc:
        logger.error(
            f"Error creating health record for patient {record_data.patient_id}: {exc}"
        )
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create health record: {exc}",
        )


async def get_patient_health_records(
    db: AsyncSession, patient_id: int, record_type: Optional[str] = None
) -> List[HealthRecord]:
    """Get all health records for a patient."""

    try:
        query = select(HealthRecord).where(HealthRecord.patient_id == patient_id)

        if record_type:
            try:
                record_type_enum = RecordType(record_type.lower())
                query = query.where(HealthRecord.record_type == record_type_enum)
            except ValueError:

                logger.warning(f"Invalid record_type filter value: {record_type}")

                pass

        query = query.order_by(HealthRecord.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    except Exception as exc:
        logger.error(f"Error retrieving health records for patient {patient_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health records.",
        )


async def get_health_record_by_id(db: AsyncSession, record_id: int) -> HealthRecord:
    """Get a specific health record by ID."""

    try:
        query = select(HealthRecord).where(HealthRecord.id == record_id)
        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if not record:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health record with ID {record_id} not found",
            )

        return record

    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        logger.error(f"Error retrieving health record {record_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health record.",
        )


async def create_triage_record_from_chats(
    db: AsyncSession, patient_id: int, doctor_id: Optional[int] = None
) -> Optional[HealthRecord]:
    """Create a triage health record based on patient's recent chat history."""
    try:

        query = (
            select(ChatSession)
            .where(ChatSession.patient_id == patient_id)
            .order_by(ChatSession.created_at.desc())
            .limit(10)
        )
        result = await db.execute(query)
        chat_sessions = result.scalars().all()

        if not chat_sessions:
            logger.info(
                f"No recent chat sessions found for patient {patient_id} to create triage record."
            )
            return None

        combined_text = "\n---\n".join(
            [
                f"Patient: {chat.input_text}\nAI: {chat.model_response or 'N/A'}"
                for chat in reversed(chat_sessions)
                if chat.input_text
            ]
        )
        if not combined_text:
            logger.info(f"No processable chat content found for patient {patient_id}.")
            return None

        from app.ai.chatbot import extract_symptoms

        symptoms_extraction = await extract_symptoms(combined_text)

        most_recent_triage = None
        for chat in chat_sessions:
            if chat.triage_advice:
                most_recent_triage = chat.triage_advice
                break

        health_record = HealthRecord(
            patient_id=patient_id,
            doctor_id=doctor_id,
            record_type=RecordType.at_triage,
            title=f"Pre-appointment Triage Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            summary=(
                f"Automated summary based on recent chat interactions ({len(chat_sessions)} messages). "
                f"Latest AI triage recommendation: {most_recent_triage or 'None provided'}."
            ),
            symptoms=symptoms_extraction.symptoms if symptoms_extraction else None,
            triage_recommendation=most_recent_triage,
            confidence_score=(
                symptoms_extraction.confidence_score if symptoms_extraction else None
            ),
            chat_session_id=chat_sessions[0].id if chat_sessions else None,
        )

        db.add(health_record)
        await db.commit()
        await db.refresh(health_record)

        logger.info(
            f"Created triage health record id={health_record.id} for patient {patient_id}"
        )
        return health_record

    except Exception as exc:
        logger.error(
            f"Error creating triage health record from chats for patient {patient_id}: {exc}"
        )
        await db.rollback()

        return None
