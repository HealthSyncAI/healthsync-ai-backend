from fastapi import APIRouter

router = APIRouter()

@router.get("/hello", tags=["Example"])
async def hello_world():
    """
    A simple endpoint confirming that our API is up and running.
    Integration Note:
    - In production, ensure this endpoint is secured or used only as a health check.
    """
    return {"message": "Hello World"}