from pydantic import BaseModel


class UsageStatistics(BaseModel):
    total_users: int
    total_doctors: int
    total_patients: int
    total_appointments: int
    total_chat_sessions: int
    total_health_records: int
    total_triage_records: int
    total_doctor_notes: int
