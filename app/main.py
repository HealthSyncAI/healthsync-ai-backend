import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, chatbot, appointment, health_record, statistics, health
from app.core.logger import setup_logging
from app.core.scheduler import scheduler_service

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HealthSync AI",
    description="A production-ready healthcare application backend.",
    version="1.0.0",

    openapi_tags=[
        {"name": "auth", "description": "Authentication operations."},
        {"name": "chatbot", "description": "AI Chatbot interactions."},
        {"name": "appointment", "description": "Manage appointments and doctor listings."},
        {"name": "health-record", "description": "Manage patient health records."},
        {"name": "statistics", "description": "Usage statistics."},
        {"name": "health", "description": "Application health checks."},
    ]
)

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(appointment.router, prefix="/api/appointment", tags=["appointment"])
app.include_router(
    health_record.router, prefix="/api/health-record", tags=["health-record"]
)
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])


@app.get("/", include_in_schema=False)
async def read_root():
    return {"message": "Welcome to HealthSync AI Backend. Visit /docs for API documentation."}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application and scheduler...")

    scheduler_service.start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application and scheduler...")

    scheduler_service.stop_scheduler()
