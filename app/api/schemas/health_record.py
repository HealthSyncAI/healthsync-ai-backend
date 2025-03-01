from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.health_record import RecordType


class SymptomItem(BaseModel):
    name: str
    severity: Optional[int] = None  # 1-10 scale
    duration: Optional[str] = None
    description: Optional[str] = None


class DiagnosisItem(BaseModel):
    name: str
    icd10_code: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None


class MedicationItem(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: Optional[str] = None
    notes: Optional[str] = None


class TreatmentPlanItem(BaseModel):
    description: str
    duration: Optional[str] = None
    follow_up: Optional[str] = None


# Base schemas
class HealthRecordBase(BaseModel):
    title: str
    summary: Optional[str] = None


# Create schemas
class HealthRecordCreate(HealthRecordBase):
    record_type: RecordType
    patient_id: int
    doctor_id: Optional[int] = None
    chat_session_id: Optional[int] = None

    symptoms: Optional[List[SymptomItem]] = None
    diagnosis: Optional[List[DiagnosisItem]] = None
    treatment_plan: Optional[List[TreatmentPlanItem]] = None
    medication: Optional[List[MedicationItem]] = None

    triage_recommendation: Optional[str] = None
    confidence_score: Optional[float] = None


class DoctorRecordCreate(HealthRecordBase):
    patient_id: int
    symptoms: List[SymptomItem]
    diagnosis: List[DiagnosisItem]
    treatment_plan: List[TreatmentPlanItem]
    medication: Optional[List[MedicationItem]] = None


# Output schemas
class HealthRecordOut(HealthRecordBase):
    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    record_type: str

    symptoms: Optional[List[Dict[str, Any]]] = None
    diagnosis: Optional[List[Dict[str, Any]]] = None
    treatment_plan: Optional[List[Dict[str, Any]]] = None
    medication: Optional[List[Dict[str, Any]]] = None

    triage_recommendation: Optional[str] = None
    confidence_score: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
