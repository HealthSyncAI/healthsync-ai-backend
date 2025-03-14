from fastapi import FastAPI
from app.core.logger import setup_logging
from app.api.routers import auth, chatbot, appointment, health_record
from fastapi.middleware.cors import CORSMiddleware
from app.core.scheduler import scheduler_service
import logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HealthSync AI",
    description="A production-ready healthcare application",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers from the API module
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(appointment.router, prefix="/api/appointment", tags=["appointment"])
app.include_router(
    health_record.router, prefix="/api/health-record", tags=["health-record"]
)


# A basic health-check endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application and scheduler...")
    scheduler_service.start_scheduler()  # Start the scheduler on app startup


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application and scheduler...")
    scheduler_service.stop_scheduler()  # Stop the scheduler on app shutdown
