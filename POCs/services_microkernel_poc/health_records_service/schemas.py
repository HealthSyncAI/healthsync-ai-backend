from pydantic import BaseModel


class HealthRecordBase(BaseModel):
    user_id: int
    record_type: str
    # data: bytes  #  In a real system, you'd handle file uploads differently


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecord(HealthRecordBase):
    id: int

    class Config:
        from_attributes = True
