import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.statistics import UsageStatistics
from app.models.appointment import Appointment
from app.models.chat_session import ChatSession
from app.models.health_record import HealthRecord, RecordType
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# --- Simple In-Memory Cache ---
_cached_stats: UsageStatistics | None = None
_cache_expiry: datetime | None = None
_cache_duration = timedelta(minutes=5)


# -----------------------------


async def generate_usage_statistics(db: AsyncSession) -> UsageStatistics:
    """
    Generate usage statistics for the platform.
    Uses a simple time-based in-memory cache.
    """
    global _cached_stats, _cache_expiry

    now = datetime.now()
    if _cached_stats and _cache_expiry and now < _cache_expiry:
        logger.info("Returning cached usage statistics.")
        return _cached_stats

    logger.info("Cache invalid or expired. Recalculating usage statistics...")
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

        current_stats = UsageStatistics(
            total_users=total_users or 0,
            total_doctors=total_doctors or 0,
            total_patients=total_patients or 0,
            total_appointments=total_appointments or 0,
            total_chat_sessions=total_chat_sessions or 0,
            total_health_records=total_health_records or 0,
            total_triage_records=total_triage_records or 0,
            total_doctor_notes=total_doctor_notes or 0,
        )

        _cached_stats = current_stats
        _cache_expiry = now + _cache_duration
        logger.info(f"Usage statistics cache updated. Expires at: {_cache_expiry}")

        return current_stats

    except Exception as exc:
        logger.error(f"Error generating usage statistics: {exc}")

        raise exc
