from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.statistics import UsageStatistics
from app.db.database import get_db_session
from app.services.auth import AuthService, oauth2_scheme
from app.services.statistics import generate_usage_statistics
from app.models.user import UserRole

router = APIRouter()


@router.get("/", response_model=UsageStatistics)
async def get_usage_stats(
    db: AsyncSession = Depends(get_db_session),
):
    """Generate usage statistics for the platform."""
    return await generate_usage_statistics(db)
