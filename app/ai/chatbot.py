import asyncio
import logging
from typing import Optional

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # Newly imported for eager loading

from app.api.schemas.chatbot import (
    ChatbotResponse,
    SymptomRequest,
    ChatSessionOut,
    ChatRoomChats,
)
from app.core.config import settings
from app.models.chat_session import ChatSession
from app.models.chat_room import ChatRoom

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
    room_number: Optional[int] = None  # Optional room number from the request


class LLMResponse(BaseModel):
    raw_response: str
    analysis: str


class ValidationResult(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None


class PipelineOutput(BaseModel):
    input_text: str
    analysis: str
    triage_advice: Optional[str] = None
    model_response: Optional[str] = None


# --- Pipeline Stages (Functions) ---


def preprocess_input(payload: SymptomRequest, current_user) -> PreprocessedInput:
    """Transformer: Preprocesses the input text."""
    clean_text = payload.symptom_text.lower().strip()  # Basic cleaning
    return PreprocessedInput(
        original_text=payload.symptom_text,
        clean_text=clean_text,
        user_id=current_user.id,
        room_number=payload.room_number,
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
    if not llm_response.analysis:
        return ValidationResult(
            is_valid=False, error_message="Empty analysis from LLM."
        )
    return ValidationResult(is_valid=True)


async def generate_triage_advice(llm_response: LLMResponse) -> Optional[str]:
    """Transformer: Generate triage advice based on analysis."""
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
    """Consumer: Saves the chat session (and creates/uses a chat room) in the database."""
    try:
        # Determine (or create) the chat room.
        if preprocessed_input.room_number is not None:
            query = select(ChatRoom).where(
                ChatRoom.patient_id == preprocessed_input.user_id,
                ChatRoom.room_number == preprocessed_input.room_number,
            )
            result = await db.execute(query)
            chat_room = result.scalar_one_or_none()
            if chat_room is None:
                chat_room = ChatRoom(
                    patient_id=preprocessed_input.user_id,
                    room_number=preprocessed_input.room_number,
                )
                db.add(chat_room)
                await db.commit()
                await db.refresh(chat_room)
        else:
            query = select(func.max(ChatRoom.room_number)).where(
                ChatRoom.patient_id == preprocessed_input.user_id
            )
            result = await db.execute(query)
            max_room = result.scalar() or 0
            new_room_number = max_room + 1
            chat_room = ChatRoom(
                patient_id=preprocessed_input.user_id, room_number=new_room_number
            )
            db.add(chat_room)
            await db.commit()
            await db.refresh(chat_room)

        chat_session = ChatSession(
            patient_id=preprocessed_input.user_id,
            input_text=preprocessed_input.original_text,
            model_response=llm_response.analysis,
            triage_advice=triage_advice,
            chat_room_id=chat_room.id,
        )
        db.add(chat_session)
        await db.commit()
        await db.refresh(chat_session)
        logger.info(
            f"Chat session recorded for user {preprocessed_input.user_id} (session id: {chat_session.id}, "
            f"chat room: {chat_room.room_number})"
        )
    except Exception as exc:
        logger.error(
            f"Error saving chat session for user {preprocessed_input.user_id}: {exc}"
        )
        # Log the error without raising to avoid failing the whole request.


async def analyze_symptoms_pipeline(
    payload: SymptomRequest, current_user, db: AsyncSession
) -> ChatbotResponse:
    """Main pipeline function."""
    preprocessed_input = preprocess_input(payload, current_user)
    llm_response = await generate_llm_response(preprocessed_input)
    validation_result = validate_response(llm_response)
    if not validation_result.is_valid:
        raise HTTPException(status_code=500, detail=validation_result.error_message)
    triage_advice = await generate_triage_advice(llm_response)
    await save_chat_session(db, preprocessed_input, llm_response, triage_advice)
    return ChatbotResponse(
        input_text=preprocessed_input.original_text,
        analysis=llm_response.analysis,
        triage_advice=triage_advice,
        model_response=llm_response.raw_response,
    )


async def get_user_chats_service(current_user, db: AsyncSession):
    """Retrieves user's chat history grouped by chat room."""
    try:
        query = (
            select(ChatSession)
            .filter(ChatSession.patient_id == current_user.id)
            .options(
                selectinload(ChatSession.chat_room)
            )  # Eagerly load the chat_room relation
            .order_by(ChatSession.created_at.desc())
        )
        result = await db.execute(query)
        chat_sessions = result.scalars().all()

        room_groups = {}
        for session in chat_sessions:
            rn = (
                session.room_number
            )  # Accesses property which now uses the eagerly loaded chat_room
            if rn not in room_groups:
                room_groups[rn] = []
            room_groups[rn].append(ChatSessionOut.from_orm(session))

        grouped_chats = [
            ChatRoomChats(room_number=rn, chats=room_groups[rn])
            for rn in sorted(room_groups.keys())
        ]
        return grouped_chats
    except Exception as exc:
        logger.error(
            f"Error retrieving chat sessions for user {current_user.username}: {exc}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat sessions.",
        )
