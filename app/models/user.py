import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum, Float, Date, Boolean
from sqlalchemy.sql import func

from app.db.database import Base


class UserRole(enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class Gender(enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.patient, nullable=False)

    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Basic health information
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    height_cm = Column(Float, nullable=True)  # Height in centimeters
    weight_kg = Column(Float, nullable=True)  # Weight in kilograms
    blood_type = Column(String(5), nullable=True)  # e.g., A+, O-, AB+
    allergies = Column(
        String(255), nullable=True
    )  # Comma-separated list, or could be a separate table
    existing_conditions = Column(
        String(255), nullable=True
    )  # Comma-separated, or separate table

    # Doctor-specific details (nullable for non-doctors)
    specialization = Column(String(100), nullable=True)
    qualifications = Column(String(200), nullable=True)
    is_available = Column(
        Boolean, default=True
    )  # Indicates if the doctor is available for appointments.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"

        # app/models/user.py
        # Add these properties to the existing User class

    @property
    def years_experience(self):
        # For now, we'll return a dummy value based on user ID to simulate variation
        if self.role != UserRole.doctor:
            return None
        return (self.id * 3) % 15 + 1  # 1-15 years of experience

    @property
    def bio(self):
        if self.role != UserRole.doctor:
            return None
        spec = self.specialization or "General Medicine"
        return f"Experienced physician specializing in {spec}. Committed to providing compassionate and comprehensive care."

    @property
    def rating(self):
        if self.role != UserRole.doctor:
            return None
        # Generate a rating between 4.0 and 5.0
        return 4.0 + ((self.id % 10) / 10)

    @property
    def expertise_areas(self):
        if not self.specialization or self.role != UserRole.doctor:
            return []
        # Generate some expertise areas based on specialization
        base_expertise = self.specialization.split(", ")
        if "Cardiology" in self.specialization:
            return base_expertise + ["Heart Disease", "Hypertension Management"]
        elif "Neurology" in self.specialization:
            return base_expertise + ["Headache Disorders", "Movement Disorders"]
        return base_expertise

    @property
    def languages(self):
        # Default languages for all doctors
        return ["English", "Spanish"] if self.role == UserRole.doctor else []
