from fastapi import FastAPI
from app.api.routers import hello
from app.core.config import settings
from app.core.logger import setup_logging

setup_logging()

app = FastAPI(
    title="HealthSync AI",
    description="A production-ready healthcare application",
    version="1.0.0"
)

# Include routers from the API module
app.include_router(hello.router, prefix="/api")

# A basic health-check endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello World"}