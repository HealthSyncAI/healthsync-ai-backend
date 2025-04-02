import logging

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthStatus:
    """Simple class to hold health status details."""

    def __init__(self):
        self.status: str = "ok"
        self.database_connected: bool = False
        self.details: dict = {}

    def set_database_status(self, connected: bool, error: str | None = None):
        self.database_connected = connected
        if error:
            self.details["database_error"] = error
            self.status = "error"

    def add_detail(self, key: str, value: any):
        self.details[key] = value

    def get_response(self) -> dict:
        return {
            "status": self.status,
            "database_connected": self.database_connected,
            "details": self.details,
        }

    def get_http_status(self) -> int:
        return (
            status.HTTP_200_OK
            if self.status == "ok"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )


@router.get(
    "/",
    tags=["health"],
    summary="Perform a health check",
    response_description="Returns the health status of the application",
)
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """
    Checks the operational status of the application, including database connectivity.
    Returns 'ok' if the application and critical services (like the database) are running.
    Returns 'error' and a 503 status code otherwise.
    """
    health = HealthStatus()
    try:
        await db.execute(select(1))
        health.set_database_status(connected=True)
        logger.info("Health check: Database connection successful.")
    except Exception as e:
        error_msg = f"Database connection failed: {e}"
        logger.error(f"Health check: {error_msg}")
        health.set_database_status(connected=False, error=error_msg)

    health.add_detail("service_name", "HealthSync AI Backend")
    health.add_detail("version", "1.0.0")

    response_body = health.get_response()
    http_status_code = health.get_http_status()

    if http_status_code != status.HTTP_200_OK:
        logger.warning(
            f"Health check returning 200 OK, but internal status is '{health.status}'"
        )

    return response_body
