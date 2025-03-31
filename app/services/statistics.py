import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.statistics import UsageStatistics
from app.models.user import User, UserRole
from app.models.appointment import Appointment
from app.models.chat_session import ChatSession
from app.models.health_record import HealthRecord, RecordType

logger = logging.getLogger(__name__)


async def generate_usage_statistics(db: AsyncSession) -> UsageStatistics:
    """Generate usage statistics for the platform."""
    try:

        total_users = await db.scalar(select(func.count()).select_from(User))
        total_doctors = await db.scalar(
            select(func.count()).select_from(User).where(User.role == UserRole.doctor)
        )
        total_patients = await db.scalar(
            select(func.count()).select_from(User).where(User.role == UserRole.patient)
        )

        total_appointments = await db.scalar(
            select(func.count()).select_from(Appointment)
        )

        total_chat_sessions = await db.scalar(
            select(func.count()).select_from(ChatSession)
        )

        total_health_records = await db.scalar(
            select(func.count()).select_from(HealthRecord)
        )
        total_triage_records = await db.scalar(
            select(func.count())
            .select_from(HealthRecord)
            .where(HealthRecord.record_type == RecordType.at_triage)
        )
        total_doctor_notes = await db.scalar(
            select(func.count())
            .select_from(HealthRecord)
            .where(HealthRecord.record_type == RecordType.doctor_note)
        )

        return UsageStatistics(
            total_users=total_users,
            total_doctors=total_doctors,
            total_patients=total_patients,
            total_appointments=total_appointments,
            total_chat_sessions=total_chat_sessions,
            total_health_records=total_health_records,
            total_triage_records=total_triage_records,
            total_doctor_notes=total_doctor_notes,
        )

    except Exception as exc:
        logger.error(f"Error generating usage statistics: {exc}")
        raise exc
