from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chatbot import SymptomRequest, ChatbotResponse, ChatSessionOut
from app.db.database import get_db_session
from app.services.auth import AuthService
from app.ai.chatbot import analyze_symptoms_pipeline, get_user_chats_service

router = APIRouter()


@router.post("/symptom", response_model=ChatbotResponse, status_code=status.HTTP_200_OK)
async def analyze_symptoms(
    payload: SymptomRequest,
    current_user=Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # --- Producer (Implicit in the FastAPI endpoint) ---
    # The FastAPI framework handles receiving the request and parsing the payload.
    try:
        return await analyze_symptoms_pipeline(payload, current_user, db)
    except Exception as e:
        # Catch any exceptions that might bubble up from the pipeline
        raise HTTPException(
            status_code=500, detail=f"An error occurred in the chatbot pipeline: {e}"
        )


@router.get(
    "/chats", response_model=List[ChatSessionOut], status_code=status.HTTP_200_OK
)
async def get_user_chats(
    current_user=Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_user_chats_service(current_user, db)
