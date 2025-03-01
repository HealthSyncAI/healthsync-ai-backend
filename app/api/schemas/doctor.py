from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import date


class DoctorBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    specialization: Optional[str] = None
    qualifications: Optional[str] = None
    email: EmailStr


class DoctorList(DoctorBase):
    is_available: bool = True
    years_experience: Optional[int] = None
    bio: Optional[str] = None
    rating: Optional[float] = None

    model_config = {"from_attributes": True}


class DoctorDetail(DoctorList):
    expertise_areas: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    education: Optional[str] = None

    model_config = {"from_attributes": True}
