import asyncio
import logging

from fastapi import HTTPException, status
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chatbot import ChatbotResponse, SymptomRequest
from app.core.config import settings
from app.models.chat_session import ChatSession

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.open_router_api_key,
)


async def analyze_symptoms_service(payload: SymptomRequest, current_user, db: AsyncSession) -> ChatbotResponse:
    try:
        loop = asyncio.get_running_loop()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a highly skilled doctor specializing in diagnosing common diseases. "
                    "Based on the patient's symptom description provided in the next message, determine "
                    "the most likely condition and provide clear recommendations on what steps to take. "
                    "Advise whether the patient should seek immediate care, schedule an appointment, or try home remedies. "
                    "Offer this guidance proactively without the patient needing to ask."
                ),
            },
            {"role": "user", "content": payload.symptom_text},
        ]
        model_response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",
                messages=messages,
            ),
        )
    except Exception as exc:
        logger.error(f"Error generating model response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the symptom text.",
        )

    try:
        analysis_text = model_response.choices[0].message.content
        triage_advice = None
        response = ChatbotResponse(
            input_text=payload.symptom_text,
            analysis=analysis_text,
            triage_advice=triage_advice,
            model_response=None,
        )
    except Exception as exc:
        logger.error(f"Error processing model response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the chatbot response.",
        )

    try:
        chat_session = ChatSession(
            patient_id=current_user.id,
            input_text=payload.symptom_text,
            model_response=str(analysis_text),
            triage_advice=triage_advice,
        )
        db.add(chat_session)
        await db.commit()
        await db.refresh(chat_session)
        logger.info(
            f"Chat session recorded for user {current_user.username} (session id: {chat_session.id})"
        )
    except Exception as exc:
        logger.error(f"Error saving chat session for user {current_user.username}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving the chat session.",
        )

    return response


async def get_user_chats_service(current_user, db: AsyncSession):
    try:
        query = (
            select(ChatSession)
            .filter(ChatSession.patient_id == current_user.id)
            .order_by(ChatSession.created_at.desc())
        )
        result = await db.execute(query)
        chat_sessions = result.scalars().all()
    except Exception as exc:
        logger.error(f"Error retrieving chat sessions for user {current_user.username}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat sessions.",
        )

    return chat_sessions
