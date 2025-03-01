import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.health_record import HealthRecordCreate
from app.models.health_record import HealthRecord, RecordType
from app.models.chat_session import ChatSession


logger = logging.getLogger(__name__)


async def create_health_record(
    db: AsyncSession, record_data: HealthRecordCreate, creator_id: int
) -> HealthRecord:
    """Create a new health record."""
    try:
        new_record = HealthRecord(
            patient_id=record_data.patient_id,
            doctor_id=record_data.doctor_id or creator_id,
            chat_session_id=record_data.chat_session_id,
            record_type=record_data.record_type,
            title=record_data.title,
            summary=record_data.summary,
            symptoms=(
                [s.dict() for s in record_data.symptoms]
                if record_data.symptoms
                else None
            ),
            diagnosis=(
                [d.dict() for d in record_data.diagnosis]
                if record_data.diagnosis
                else None
            ),
            treatment_plan=(
                [t.dict() for t in record_data.treatment_plan]
                if record_data.treatment_plan
                else None
            ),
            medication=(
                [m.dict() for m in record_data.medication]
                if record_data.medication
                else None
            ),
            triage_recommendation=record_data.triage_recommendation,
            confidence_score=record_data.confidence_score,
        )

        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)

        logger.info(
            f"Created health record id={new_record.id} for patient {record_data.patient_id}"
        )
        return new_record

    except Exception as exc:
        logger.error(f"Error creating health record: {exc}")
        await db.rollback()
        raise exc


async def get_patient_health_records(
    db: AsyncSession, patient_id: int, record_type: Optional[str] = None
) -> List[HealthRecord]:
    """Get all health records for a patient."""
    try:
        query = select(HealthRecord).where(HealthRecord.patient_id == patient_id)

        # Filter by record type if provided
        if record_type:
            try:
                record_type_enum = RecordType(record_type)
                query = query.where(HealthRecord.record_type == record_type_enum)
            except ValueError:
                # Invalid record type - ignore filter
                pass

        # Order by created date, newest first
        query = query.order_by(HealthRecord.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    except Exception as exc:
        logger.error(f"Error retrieving health records for patient {patient_id}: {exc}")
        raise exc


async def get_health_record_by_id(db: AsyncSession, record_id: int) -> HealthRecord:
    """Get a specific health record by ID."""
    try:
        query = select(HealthRecord).where(HealthRecord.id == record_id)
        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError(f"Health record with ID {record_id} not found")

        return record

    except Exception as exc:
        logger.error(f"Error retrieving health record {record_id}: {exc}")
        raise exc


async def create_triage_record_from_chats(
    db: AsyncSession, patient_id: int, doctor_id: Optional[int] = None
) -> Optional[HealthRecord]:
    """Create a triage health record based on patient's chat history."""
    try:
        # Get the patient's recent chat sessions
        query = (
            select(ChatSession)
            .where(ChatSession.patient_id == patient_id)
            .order_by(ChatSession.created_at.desc())
            .limit(10)  # Get the 10 most recent chats
        )
        result = await db.execute(query)
        chat_sessions = result.scalars().all()

        if not chat_sessions:
            logger.info(f"No chat sessions found for patient {patient_id}")
            return None

        # Combine the chat history for analysis
        combined_text = "\n".join(
            [
                f"Patient: {chat.input_text}\nAI: {chat.model_response}"
                for chat in chat_sessions
                if chat.input_text and chat.model_response
            ]
        )

        # Extract structured symptoms from the combined chat
        from app.ai.chatbot import extract_symptoms

        symptoms_extraction = await extract_symptoms(combined_text)

        # Get the most recent triage advice
        most_recent_triage = None
        for chat in chat_sessions:
            if chat.triage_advice:
                most_recent_triage = chat.triage_advice
                break

        # Create a preliminary health record
        health_record = HealthRecord(
            patient_id=patient_id,
            doctor_id=doctor_id,  # May be None for now, doctor will be assigned later
            record_type=RecordType.at_triage,
            title=f"Pre-appointment Assessment - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            summary=f"Summary of recent patient chat interactions. Latest triage: {most_recent_triage}",
            symptoms=symptoms_extraction.symptoms,
            triage_recommendation=most_recent_triage,
            confidence_score=symptoms_extraction.confidence_score,
        )

        db.add(health_record)
        await db.commit()
        await db.refresh(health_record)

        logger.info(
            f"Created triage health record id={health_record.id} for patient {patient_id}"
        )
        return health_record

    except Exception as exc:
        logger.error(f"Error creating triage health record from chats: {exc}")
        await db.rollback()
        return None
