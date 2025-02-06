import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from transformers import pipeline

from app.db.database import get_db_session
from app.services.auth import get_current_user  # Updated dependency import

# Setup a basic logger.
logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chatbot"])


# Request Pydantic model for receiving the user's symptom text.
class SymptomRequest(BaseModel):
    symptom_text: str


# Response Pydantic model for returning a structured chatbot response.
class ChatbotResponse(BaseModel):
    input_text: str
    analysis: str
    triage_advice: Optional[str] = None  # Optional field for additional processing.
    model_response: dict


# Instantiate the Hugging Face pipeline.
chatbot_pipe = pipeline("text-generation", model="microsoft/DialoGPT-medium")


@router.post("/symptom", response_model=ChatbotResponse, status_code=status.HTTP_200_OK)
async def analyze_symptoms(
        payload: SymptomRequest,
        current_user=Depends(get_current_user),  # Now using the centralized dependency
        db: AsyncSession = Depends(get_db_session)
):
    """
    Receives a user symptom text, processes it through the DialoGPT model,
    persists the chat session, and returns the analysis.
    """
    try:
        loop = asyncio.get_running_loop()
        model_response = await loop.run_in_executor(
            None,
            lambda: chatbot_pipe(
                payload.symptom_text,
                max_length=100,
                num_return_sequences=1,
                truncation=True  # Ensure proper truncation.
            )
        )
    except Exception as exc:
        logger.error(f"Error generating model response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the symptom text."
        )

    try:
        analysis_text = ""
        if isinstance(model_response, list) and model_response:
            analysis_text = model_response[0].get("generated_text", "")
        triage_advice = None  # No triage advice from the model currently.
        model_response_dict = model_response[0] if isinstance(model_response, list) else model_response

        result = ChatbotResponse(
            input_text=payload.symptom_text,
            analysis=analysis_text,
            triage_advice=triage_advice,
            model_response=model_response_dict
        )
    except Exception as exc:
        logger.error(f"Error processing model response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the chatbot response."
        )

    # Persist the chat session details in the database.
    try:
        from app.models.chat_session import ChatSession  # Ensure ChatSession model is defined appropriately.
        chat_session = ChatSession(
            patient_id=current_user.id,  # Link the session to the authenticated user.
            input_text=payload.symptom_text,
            deepseek_response=str(model_response),  # Store model output as a string.
            triage_advice=triage_advice
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
            detail="An error occurred while saving the chat session."
        )

    return result
