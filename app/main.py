from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import setup_logging
from app.api.routers import auth, chatbot

setup_logging()

app = FastAPI(
    title="HealthSync AI",
    description="A production-ready healthcare application",
    version="1.0.0",
)

# Include routers from the API module
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])


# A basic health-check endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello World"}
