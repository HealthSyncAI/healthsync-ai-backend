from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chatbot import SymptomRequest, ChatbotResponse, ChatSessionOut
from app.db.database import get_db_session
from app.services.auth import AuthService
from app.ai.chatbot import analyze_symptoms_service, get_user_chats_service

router = APIRouter()


@router.post("/symptom", response_model=ChatbotResponse, status_code=status.HTTP_200_OK)
async def analyze_symptoms(
    payload: SymptomRequest,
    current_user=Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    return await analyze_symptoms_service(payload, current_user, db)


@router.get(
    "/chats", response_model=List[ChatSessionOut], status_code=status.HTTP_200_OK
)
async def get_user_chats(
    current_user=Depends(AuthService.get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_user_chats_service(current_user, db)
