from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date
from app.models.user import Gender, UserRole


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    role: UserRole = UserRole.patient


class Token(BaseModel):
    access_token: str
    token_type: str
