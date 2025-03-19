from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Mock user database (In a real application, use a real database)
users = {
    1: {"user_id": 1, "username": "patient1", "password": "password1"},
    2: {"user_id": 2, "username": "doctor1", "password": "password2"},
}


class AuthRequest(BaseModel):
    user_id: int


@app.post("/authenticate")
async def authenticate(auth_request: AuthRequest):
    """
    Authenticates a user and returns a mock token.
    """
    user = users.get(auth_request.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # In a real application, generate a JWT token here
    return {"token": "mock_token_123"}
