from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()


class SymptomRequest(BaseModel):
    symptom: str


def verify_token(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    if token != "mock_token_123":  # Validate the mock token
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/check_symptom")
async def check_symptom(symptom_request: SymptomRequest, authorization: Optional[str] = Header(None)):
    """
    Provides a simplified symptom check (mocked).
    """
    verify_token(authorization)
    # Mock symptom checking logic
    if "fever" in symptom_request.symptom.lower():
        recommendation = "See a doctor"
    elif "cough" in symptom_request.symptom.lower():
        recommendation = "Take some rest and drink water"
    else:
        recommendation = "No major concerns detected"
    return {"recommendation": recommendation}
