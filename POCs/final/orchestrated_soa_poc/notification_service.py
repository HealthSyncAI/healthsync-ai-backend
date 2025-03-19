from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()


class NotificationRequest(BaseModel):
    patient_id: int
    message: str


def verify_token(authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.split(" ")[1]
    if token != "mock_token_123":  # Validate the mock token
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/notify")
async def send_notification(
    notification_request: NotificationRequest,
    authorization: Optional[str] = Header(None),
):
    verify_token(authorization)
    print(
        f"Sending notification to patient {notification_request.patient_id}: {notification_request.message}"
    )
    return {"status": "Notification sent"}
