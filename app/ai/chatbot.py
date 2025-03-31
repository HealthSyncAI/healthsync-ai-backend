import asyncio
import json
import logging
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.chatbot import (
    ChatbotResponse,
    SymptomRequest,
    ChatSessionOut,
    ChatRoomChats,
)
from app.core.config import settings
from app.models.chat_room import ChatRoom
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
    room_number: Optional[int] = None


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


class SymptomExtraction(BaseModel):
    symptoms: List[Dict[str, Any]]
    confidence_score: float


# --- Pipeline Stages (Functions) ---


def preprocess_input(payload: SymptomRequest, current_user) -> PreprocessedInput:
    """Transformer: Preprocesses the input text."""
    clean_text = payload.symptom_text.lower().strip()
    return PreprocessedInput(
        original_text=payload.symptom_text,
        clean_text=clean_text,
        user_id=current_user.id,
        room_number=payload.room_number,
    )


async def generate_llm_response(preprocessed_input: PreprocessedInput) -> LLMResponse:
    """Transformer: Interacts with the LLM using an enhanced system prompt.

    The system prompt instructs the model to assume a doctor persona and to begin its answer with a specific
    keyword (TRIAGE_IMMEDIATE, TRIAGE_SCHEDULE, or TRIAGE_SELF_CARE) to denote the triage outcome.
    """
    try:
        loop = asyncio.get_running_loop()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a highly qualified medical doctor with extensive expertise in diagnosing common "
                    "ailments and providing accurate, actionable recommendations. Read the patient's symptom "
                    "description carefully and then provide a concise evaluation that includes a clear recommendation. "
                    "IMPORTANT: Begin your response with one keyword that precisely indicates the appropriate triage: "
                    "'TRIAGE_IMMEDIATE' if the patient should seek immediate emergency care, "
                    "'TRIAGE_SCHEDULE' if scheduling a doctor’s appointment is advised, or "
                    "'TRIAGE_SELF_CARE' if the symptoms can be managed with self-care/home remedies. "
                    "Your answer should then follow with detailed yet focused advice."
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
    """Transformer: Generate triage advice based on analysis.

    This function checks the language model output for keywords that indicate a level
    of urgency and returns a corresponding triage recommendation.
    """
    analysis_text = llm_response.analysis.upper()
    if "TRIAGE_IMMEDIATE" in analysis_text:
        return "seek_immediate_care"
    elif "TRIAGE_SCHEDULE" in analysis_text:
        return "schedule_appointment"
    elif "TRIAGE_SELF_CARE" in analysis_text:
        return "self_care_recommended"

    return None


async def save_chat_session(
    db: AsyncSession,
    preprocessed_input: PreprocessedInput,
    llm_response: LLMResponse,
    triage_advice: Optional[str],
) -> Optional[ChatSession]:
    """Consumer: Saves the chat session (and creates/uses a chat room) in the database."""
    try:
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
        return chat_session
    except Exception as exc:
        logger.error(
            f"Error saving chat session for user {preprocessed_input.user_id}: {exc}"
        )
        return None


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
            rn = session.room_number
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


async def extract_symptoms(symptom_text: str) -> SymptomExtraction:
    """Extract structured symptoms from the patient's input using LLM."""
    try:
        loop = asyncio.get_running_loop()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical symptom analyzer. Extract symptoms from the patient's description. "
                    "For each symptom, identify: name, severity (1-10 if mentioned), duration (if mentioned), "
                    "and any specific description. Return ONLY JSON in this format: "
                    "{'symptoms': [{'name': 'symptom name', 'severity': severity_number, "
                    "'duration': 'duration_text', 'description': 'specific_details'}], "
                    "'confidence_score': float_between_0_and_1}"
                ),
            },
            {"role": "user", "content": symptom_text},
        ]

        model_response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",
                messages=messages,
                response_format={"type": "json_object"},
            ),
        )

        extraction_text = model_response.choices[0].message.content
        try:
            extraction_data = json.loads(extraction_text)
            return SymptomExtraction(
                symptoms=extraction_data.get("symptoms", []),
                confidence_score=extraction_data.get("confidence_score", 0.5),
            )
        except json.JSONDecodeError:
            logger.error(f"Failed to parse symptom extraction: {extraction_text}")
            return SymptomExtraction(symptoms=[], confidence_score=0.0)

    except Exception as exc:
        logger.error(f"Error in symptom extraction: {exc}")
        return SymptomExtraction(symptoms=[], confidence_score=0.0)
