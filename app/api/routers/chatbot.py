import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from openai import OpenAI

from app.db.database import get_db_session
from app.services.auth import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class SymptomRequest(BaseModel):
    symptom_text: str


class ChatbotResponse(BaseModel):
    input_text: str
    analysis: str
    triage_advice: Optional[str] = None
    model_response: Optional[str] = None


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.open_router_api_key,
)


@router.post("/symptom", response_model=ChatbotResponse, status_code=status.HTTP_200_OK)
async def analyze_symptoms(
    payload: SymptomRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Receives the user's symptom text, sends it along with a system message to instruct the model
    to act as a doctor. The model then returns a possible diagnosis along with next-step suggestions.
    The endpoint persists the chat session details and returns the structured response.
    """
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

        result = ChatbotResponse(
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
        from app.models.chat_session import ChatSession

        chat_session = ChatSession(
            patient_id=current_user.id,
            input_text=payload.symptom_text,
            deepseek_response=str(analysis_text),
            triage_advice=triage_advice,
        )
        db.add(chat_session)
        await db.commit()
        await db.refresh(chat_session)
        logger.info(
            f"Chat session recorded for user {current_user.username} (session id: {chat_session.id})"
        )
    except Exception as exc:
        logger.error(
            f"Error saving chat session for user {current_user.username}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving the chat session.",
        )

    return result
