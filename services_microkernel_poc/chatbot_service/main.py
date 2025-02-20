from fastapi import Depends, FastAPI, HTTPException

from . import schemas
from .plugins import huggingface_plugin, triage_plugin, voice_plugin
from .database import SessionLocal, engine
from . import models, crud
from sqlalchemy.orm import Session
from datetime import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/chat/", response_model=schemas.ChatResponse)
async def chat_endpoint(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 1.  Basic Interaction (Core System)
    print(f"Received input: {request.user_input}")

    # Check if it is a voice message
    if voice_plugin.is_voice_input(request.user_input):
        transcribed_text = await voice_plugin.process_voice_input(request.user_input)
        if transcribed_text is None:
            return schemas.ChatResponse(response="Could not understand voice input.")
        user_input = transcribed_text
    else:
        user_input = request.user_input

    # Create a chat session
    chat_session = crud.create_chat_session(
        db=db,
        chat_session=schemas.ChatSessionCreate(
            user_id=1, start_time=datetime.now(), messages=user_input
        ),
    )

    # 2.  Hugging Face Plugin
    hf_response = await huggingface_plugin.get_huggingface_response(user_input)

    # 3. Triage Plugin
    triage_result = triage_plugin.apply_triage_rules(user_input, hf_response)

    # 4. Formulate response (Core System)
    final_response = triage_result  # Or combine/format as needed

    # Update the messages
    chat_session = crud.update_chat_session(
        db=db, chat_session_id=chat_session.id, updated_messages=final_response
    )

    return schemas.ChatResponse(response=final_response)
