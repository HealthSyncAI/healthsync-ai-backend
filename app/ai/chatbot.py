import asyncio
import logging
from typing import Optional

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.chatbot import ChatbotResponse, SymptomRequest, ChatSessionOut
from app.core.config import settings
from app.models.chat_session import ChatSession

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.open_router_api_key,
)


# --- Data Models (for Pipeline Stages) ---


class PreprocessedInput(BaseModel):
    original_text: str
    clean_text: str
    user_id: int


class LLMResponse(BaseModel):
    raw_response: str
    analysis: str
    #  triage_advice: Optional[str] = None # Removed as it is not used.


class ValidationResult(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None


class PipelineOutput(BaseModel):  # Combine the ChatbotResponse and the recommendation
    input_text: str
    analysis: str
    triage_advice: Optional[str] = None
    model_response: Optional[str] = None


# --- Pipeline Stages (Functions) ---


def preprocess_input(payload: SymptomRequest, current_user) -> PreprocessedInput:
    """Transformer: Preprocesses the input text."""
    clean_text = payload.symptom_text.lower().strip()  # Basic cleaning
    # Add more preprocessing steps as needed (stemming, lemmatization, etc.)
    return PreprocessedInput(
        original_text=payload.symptom_text,
        clean_text=clean_text,
        user_id=current_user.id,
    )


async def generate_llm_response(preprocessed_input: PreprocessedInput) -> LLMResponse:
    """Transformer: Interacts with the LLM."""
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
            {"role": "user", "content": preprocessed_input.clean_text},
        ]
        model_response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",
                messages=messages,
            ),
        )
        analysis_text = model_response.choices[0].message.content
        return LLMResponse(raw_response=str(model_response), analysis=analysis_text)

    except Exception as exc:
        logger.error(f"Error generating model response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the symptom text.",
        )


def validate_response(llm_response: LLMResponse) -> ValidationResult:
    """Tester: Validates the LLM response."""
    # Implement your validation logic here.  This is crucial for a real-world application.
    if not llm_response.analysis:
        return ValidationResult(
            is_valid=False, error_message="Empty analysis from LLM."
        )
    # Add more checks: consistency, safety, etc.
    return ValidationResult(is_valid=True)


async def generate_triage_advice(llm_response: LLMResponse) -> Optional[str]:
    """Transformer: Generate triage advice based on analysis."""
    # Implement your triage logic here.  This is a placeholder.
    # This is where you'd analyze the `llm_response.analysis` and determine
    # whether the user should seek immediate care, schedule an appointment, etc.
    # This is a placeholder for demonstration.
    if "immediate care" in llm_response.analysis.lower():
        return "seek_immediate_care"
    elif "schedule an appointment" in llm_response.analysis.lower():
        return "schedule_appointment"
    else:
        return None


async def save_chat_session(
    db: AsyncSession,
    preprocessed_input: PreprocessedInput,
    llm_response: LLMResponse,
    triage_advice: Optional[str],
) -> None:
    """Consumer: Saves the chat session to the database."""
    try:
        chat_session = ChatSession(
            patient_id=preprocessed_input.user_id,
            input_text=preprocessed_input.original_text,
            model_response=llm_response.analysis,  # Store the analysis
            triage_advice=triage_advice,
        )
        db.add(chat_session)
        await db.commit()
        await db.refresh(chat_session)
        logger.info(
            f"Chat session recorded for user {preprocessed_input.user_id} (session id: {chat_session.id})"
        )
    except Exception as exc:
        logger.error(
            f"Error saving chat session for user {preprocessed_input.user_id}: {exc}"
        )
        #  Don't raise here; log the error and continue.  We don't want to fail the entire
        #  request because of a database issue.  Consider a retry mechanism.
        # raise HTTPException( # Removed to prevent the whole pipeline from failing
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail="An error occurred while saving the chat session.",
        # )


async def analyze_symptoms_pipeline(
    payload: SymptomRequest, current_user, db: AsyncSession
) -> ChatbotResponse:
    """Main pipeline function."""

    # --- Producer (Data from the request) ---
    #   The producer is implicitly handled by the FastAPI framework in the router.

    # --- Transformer (Stage 1: Preprocess Input) ---
    preprocessed_input = preprocess_input(payload, current_user)

    # --- Transformer (Stage 2: Generate LLM Response) ---
    llm_response = await generate_llm_response(preprocessed_input)

    # --- Tester (Stage 3: Validate Response) ---
    validation_result = validate_response(llm_response)
    if not validation_result.is_valid:
        raise HTTPException(status_code=500, detail=validation_result.error_message)

    # --- Transformer (Stage 4: Generate Triage Advice) ---
    triage_advice = await generate_triage_advice(llm_response)

    # --- Consumer (Stage 5: Save Chat Session) ---
    await save_chat_session(db, preprocessed_input, llm_response, triage_advice)

    # --- Consumer (Stage 6: Prepare and Return Response) ---
    return ChatbotResponse(
        input_text=preprocessed_input.original_text,
        analysis=llm_response.analysis,
        triage_advice=triage_advice,
        model_response=llm_response.raw_response,  # Include raw response if needed
    )


async def get_user_chats_service(current_user, db: AsyncSession):
    """Retrieves user's chat history (unchanged, but included for completeness)."""
    try:
        query = (
            select(ChatSession)
            .filter(ChatSession.patient_id == current_user.id)
            .order_by(ChatSession.created_at.desc())
        )
        result = await db.execute(query)
        chat_sessions = result.scalars().all()
        # Convert ORM objects to Pydantic models for the response
        return [ChatSessionOut.from_orm(session) for session in chat_sessions]
    except Exception as exc:
        logger.error(
            f"Error retrieving chat sessions for user {current_user.username}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat sessions.",
        )
