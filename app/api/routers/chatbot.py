from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chatbot import SymptomRequest, ChatbotResponse, ChatSessionOut
from app.db.database import get_db_session
from app.services.auth import AuthService, oauth2_scheme
from app.ai.chatbot import analyze_symptoms_pipeline, get_user_chats_service

router = APIRouter()


@router.post("/symptom", response_model=ChatbotResponse, status_code=status.HTTP_200_OK)
async def analyze_symptoms(
    payload: SymptomRequest,
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    # Retrieve the current user by passing the token to the AuthService instance.
    current_user = await auth_service.get_current_user(token)
    try:
        return await analyze_symptoms_pipeline(payload, current_user, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred in the chatbot pipeline: {e}"
        )


@router.get(
    "/chats", response_model=List[ChatSessionOut], status_code=status.HTTP_200_OK
)
async def get_user_chats(
    auth_service: AuthService = Depends(AuthService),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
):
    # Retrieve the current user by passing the token to the AuthService instance.
    current_user = await auth_service.get_current_user(token)
    return await get_user_chats_service(current_user, db)
