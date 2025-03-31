import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def get_available_doctors(
    db: AsyncSession, specialization: Optional[str] = None
) -> List[User]:
    """Get a list of available doctors, optionally filtered by specialization."""
    try:
        query = select(User).where(
            User.role == UserRole.doctor,
            User.is_available == True,
        )

        if specialization:
            query = query.where(User.specialization.ilike(f"%{specialization}%"))

        query = query.order_by(User.last_name, User.first_name)

        result = await db.execute(query)
        doctors = result.scalars().all()

        return doctors

    except Exception as exc:
        logger.error(f"Error retrieving doctors: {exc}")
        raise exc


async def get_doctor_by_id(db: AsyncSession, doctor_id: int) -> Optional[User]:
    """Get detailed information about a specific doctor."""
    try:
        query = select(User).where(User.id == doctor_id, User.role == UserRole.doctor)

        result = await db.execute(query)
        doctor = result.scalar_one_or_none()

        return doctor

    except Exception as exc:
        logger.error(f"Error retrieving doctor with ID {doctor_id}: {exc}")
        raise exc


def calculate_experience(doctor: User) -> int:
    """Calculate years of experience if not explicitly stored."""

    if hasattr(doctor, "years_in_practice") and doctor.years_in_practice:
        return doctor.years_in_practice

    return 0
